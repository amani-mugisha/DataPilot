"""
Views for the cleaner app.

The view layer coordinates the cleaning workflow while delegating
file importing, dataset analysis, cleaning, and report generation
to their respective services.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.http import FileResponse, HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from apps.cleaner.models import CleaningJob
from apps.cleaner.services import CleaningPipeline
from apps.datasets.models import Dataset
from apps.datasets.services import analyze_dataset
from apps.importer.services.import_service import ImportService

logger = logging.getLogger(__name__)

import_service = ImportService()


def upload(request: HttpRequest) -> HttpResponse:
    """
    Accept a file upload, import it through the importer layer,
    analyze the resulting DataFrame, and show the scan-results page.

    At the moment the importer supports CSV. Additional formats will
    be added later without changing the cleaning pipeline.
    """

    if request.method != "POST":
        return render(request, "cleaner/upload.html")

    uploaded_file = request.FILES.get("file")

    try:
        # ---------------------------------------------------------
        # IMPORT LAYER
        # File -> detected format -> DataFrame
        # ---------------------------------------------------------
        dataframe, detected_file = import_service.read(
            file_path=uploaded_file,
            filename=uploaded_file.name,
            mime_type=getattr(uploaded_file, "content_type", None),
            file_size=uploaded_file.size,
        )
        

    except Exception as exc:
        logger.warning(
            "Failed to import uploaded file '%s': %s",
            uploaded_file.name,
            exc,
        )
        messages.error(
            request,
            f"Could not read this file: {exc}",
        )
        return render(request, "cleaner/upload.html")

    try:
        # ---------------------------------------------------------
        # DATASET SCAN
        # ---------------------------------------------------------
        scan = _scan_dataframe(dataframe)

        # ---------------------------------------------------------
        # DATASET RECORD
        # ---------------------------------------------------------
        dataset = Dataset.objects.create(
            name=uploaded_file.name,
            original_file=uploaded_file,
            file_size=uploaded_file.size,
            row_count=scan["rows"],
            column_count=scan["columns"],
            status=Dataset.Status.UPLOADED,
        )

        # Analyze the DataFrame directly.
        analyze_dataset(dataset, dataframe)

        # ---------------------------------------------------------
        # CLEANING JOB
        # ---------------------------------------------------------
        job = CleaningJob.objects.create(
            dataset=dataset,
            original_file=dataset.original_file,
            row_count=scan["rows"],
            status=CleaningJob.Status.PENDING,
        )

        # ---------------------------------------------------------
        # SESSION STATE
        # ---------------------------------------------------------
        request.session["dataset_id"] = dataset.id
        request.session["cleaning_job_id"] = job.id
        request.session["uploaded_file_path"] = dataset.original_file.path
        request.session["original_filename"] = uploaded_file.name
        request.session["detected_format"] = detected_file.format

        context = {
            **scan,
            "dataset": dataset,
            "job": job,
            "detected_file": detected_file,
        }

        return render(
            request,
            "cleaner/results.html",
            context,
        )

    except Exception as exc:
        logger.exception(
            "Failed while preparing uploaded file '%s'",
            uploaded_file.name,
        )

        messages.error(
            request,
            f"Could not analyze this file: {exc}",
        )

        return render(
            request,
            "cleaner/upload.html",
        )


def clean_file(request: HttpRequest) -> HttpResponse:
    """Run the cleaning pipeline on the session's pending job."""

    if request.method != "POST":
        return redirect("cleaner:upload")

    session_data, error = _get_session_job_data(request)

    if error:
        messages.error(request, error)
        return redirect("cleaner:upload")

    try:
        job = (
            CleaningJob.objects
            .select_related("dataset")
            .get(id=session_data["job_id"])
        )

    except CleaningJob.DoesNotExist:
        messages.error(
            request,
            "The cleaning job could not be found.",
        )
        return redirect("cleaner:upload")

    try:
        return _run_cleaning_pipeline(
            request,
            job,
            session_data,
        )

    except Exception as exc:
        logger.exception(
            "Cleaning job %s failed",
            job.id,
        )

        _mark_job_failed(
            job,
            str(exc),
        )

        messages.error(
            request,
            f"Could not clean this file: {exc}",
        )

        return redirect("cleaner:upload")


def download_csv(request: HttpRequest) -> HttpResponse:
    """Download the cleaned CSV."""

    return _download_session_file(
        request,
        session_key="cleaned_csv_path",
        content_type="text/csv",
        missing_message="The cleaned CSV file is no longer available.",
    )


def download_pdf(request: HttpRequest) -> HttpResponse:
    """Download the cleaning PDF report."""

    return _download_session_file(
        request,
        session_key="cleaned_pdf_path",
        content_type="application/pdf",
        missing_message="The PDF report is no longer available.",
    )


def _scan_dataframe(df) -> dict:
    """Generate lightweight statistics for the scan-results page."""

    return {
        "rows": len(df),
        "columns": len(df.columns),
        "missing_values": int(
            df.isna().sum().sum()
        ),
        "duplicate_rows": int(
            df.duplicated().sum()
        ),
    }


def _get_session_job_data(
    request: HttpRequest,
) -> tuple[dict, str | None]:

    file_path = request.session.get(
        "uploaded_file_path"
    )

    job_id = request.session.get(
        "cleaning_job_id"
    )

    if not file_path:
        return {}, "No uploaded CSV file was found."

    if not job_id:
        return {}, "No cleaning job was found."

    return {
        "file_path": file_path,
        "job_id": job_id,
        "original_filename": request.session.get(
            "original_filename",
            "uploaded.csv",
        ),
    }, None


def _run_cleaning_pipeline(
    request: HttpRequest,
    job: CleaningJob,
    session_data: dict,
) -> HttpResponse:
    """Run the cleaning pipeline and render the results."""

    pipeline = CleaningPipeline(job)

    result = pipeline.run()

    request.session["cleaned_csv_path"] = (
        result["csv_path"]
    )

    request.session["cleaned_pdf_path"] = (
        result["pdf_path"]
    )

    request.session["statistics"] = (
        result["statistics"]
    )

    context = {
        "statistics": result["statistics"],
        "csv_filename": result["csv_filename"],
        "pdf_filename": result["pdf_filename"],
        "job": job,
        "dataset": job.dataset,
    }

    return render(
        request,
        "cleaner/clean_results.html",
        context,
    )

def _download_session_file(
    request: HttpRequest,
    *,
    session_key: str,
    content_type: str,
    missing_message: str,
) -> HttpResponse:

    file_path = request.session.get(
        session_key
    )

    if not file_path or not os.path.exists(file_path):
        messages.error(
            request,
            missing_message,
        )

        return redirect(
            "cleaner:upload"
        )

    return FileResponse(
        open(file_path, "rb"),
        as_attachment=True,
        filename=os.path.basename(file_path),
        content_type=content_type,
    )
