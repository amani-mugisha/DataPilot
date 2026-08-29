"""
Views for the cleaner app.

The view layer coordinates HTTP requests while delegating dataset
ingestion, cleaning, exporting, and lifecycle management to services.

Persistent dataset/job/output state lives in the database.
The session stores only identifiers required to continue the workflow.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from django.contrib import messages
from django.http import FileResponse, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.cleaner.models import CleaningJob, CleaningJobOutput
from apps.cleaner.services import CleaningPipeline
from apps.datasets.services import DatasetIngestionService


logger = logging.getLogger(__name__)


def upload(request: HttpRequest) -> HttpResponse:
    """
    Accept an uploaded dataset and display its initial analysis.
    """

    if request.method != "POST":
        return render(
            request,
            "cleaner/upload.html",
        )

    uploaded_file = request.FILES.get("file")

    if uploaded_file is None:
        messages.error(
            request,
            "Please select a file to upload.",
        )

        return render(
            request,
            "cleaner/upload.html",
        )

    try:
        ingestion = DatasetIngestionService().ingest(
            name=uploaded_file.name,
            uploaded_file=uploaded_file,
        )

    except Exception:
        logger.exception(
            "Dataset ingestion failed for '%s'",
            getattr(
                uploaded_file,
                "name",
                "unknown",
            ),
        )

        messages.error(
            request,
            "Could not process this file.",
        )

        return render(
            request,
            "cleaner/upload.html",
        )

    dataset = ingestion.dataset
    job = ingestion.cleaning_job
    detected_file = ingestion.import_result

    request.session["dataset_id"] = dataset.pk
    request.session["cleaning_job_id"] = job.pk

    context = {
        **_scan_dataframe(
            ingestion.import_result.dataframe,
        ),
        "dataset": dataset,
        "job": job,
        "detected_file": detected_file,
    }

    return render(
        request,
        "cleaner/results.html",
        context,
    )


@require_POST
def clean_file(request: HttpRequest) -> HttpResponse:
    """
    Execute the cleaning pipeline for the current session job.
    """

    job, error_response = _get_current_job_response(
        request,
    )

    if error_response is not None:
        return error_response

    assert job is not None

    try:
        return _run_cleaning_pipeline(
            request,
            job,
        )

    except Exception as exc:
        logger.exception(
            "Cleaning job %s failed",
            job.pk,
        )

        _mark_job_failed(
            job,
            str(exc),
        )

        messages.error(
            request,
            f"Could not clean this file: {exc}",
        )

        return redirect(
            "cleaner:upload",
        )


def download_csv(request: HttpRequest) -> HttpResponse:
    """
    Download the CSV output belonging to the current cleaning job.
    """

    return _download_output(
        request,
        output_format=CleaningJobOutput.Format.CSV,
        content_type="text/csv",
        expected_suffix=".csv",
        missing_message=(
            "The cleaned CSV file is no longer available."
        ),
    )


def download_excel(request: HttpRequest) -> HttpResponse:
    """
    Download the Excel output belonging to the current cleaning job.
    """

    return _download_output(
        request,
        output_format=CleaningJobOutput.Format.XLSX,
        content_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        expected_suffix=".xlsx",
        missing_message=(
            "The cleaned Excel file is no longer available."
        ),
    )


def download_pdf(request: HttpRequest) -> HttpResponse:
    """
    Download the PDF report belonging to the current cleaning job.
    """

    return _download_output(
        request,
        output_format=CleaningJobOutput.Format.PDF,
        content_type="application/pdf",
        expected_suffix=".pdf",
        missing_message=(
            "The PDF report is no longer available."
        ),
    )


def _scan_dataframe(df: Any) -> dict[str, int]:
    """
    Generate lightweight statistics for the scan-results page.
    """

    return {
        "rows": len(df),
        "columns": len(df.columns),
        "missing_values": int(
            df.isna().sum().sum(),
        ),
        "duplicate_rows": int(
            df.duplicated().sum(),
        ),
    }


def _get_session_job_data(
    request: HttpRequest,
) -> tuple[dict[str, Any], str | None]:
    """
    Resolve the current dataset and cleaning-job identifiers.
    """

    dataset_id = request.session.get(
        "dataset_id",
    )

    job_id = request.session.get(
        "cleaning_job_id",
    )

    if not dataset_id:
        return {}, "No uploaded dataset was found."

    if not job_id:
        return {}, "No cleaning job was found."

    return {
        "dataset_id": dataset_id,
        "job_id": job_id,
    }, None


def _get_current_job_response(
    request: HttpRequest,
) -> tuple[CleaningJob | None, HttpResponse | None]:
    """
    Resolve the current cleaning job securely from session identifiers.

    A missing job returns 404.
    A job belonging to another dataset is rejected and redirects to upload.
    """

    session_data, error = _get_session_job_data(
        request,
    )

    if error:
        messages.error(
            request,
            error,
        )

        return None, redirect(
            "cleaner:upload",
        )

    job = get_object_or_404(
        CleaningJob.objects.select_related("dataset"),
        pk=session_data["job_id"],
    )

    if job.dataset_id != session_data["dataset_id"]:
        logger.warning(
            "Cleaning job %s does not belong to dataset %s",
            job.pk,
            session_data["dataset_id"],
        )

        messages.error(
            request,
            "The selected cleaning job does not belong to this dataset.",
        )

        return None, redirect(
            "cleaner:upload",
        )

    return job, None


def _run_cleaning_pipeline(
    request: HttpRequest,
    job: CleaningJob,
) -> HttpResponse:
    """
    Execute the cleaning pipeline and render the completed result.
    """

    pipeline = CleaningPipeline(job)

    result = pipeline.run()

    request.session["statistics"] = result["statistics"]

    job.refresh_from_db()

    context = {
        "statistics": result["statistics"],
        "csv_filename": result["csv_filename"],
        "xlsx_filename": result["xlsx_filename"],
        "pdf_filename": result["pdf_filename"],
        "job": job,
        "dataset": job.dataset,
    }

    return render(
        request,
        "cleaner/clean_results.html",
        context,
    )


def _download_output(
    request: HttpRequest,
    *,
    output_format: str,
    content_type: str,
    expected_suffix: str,
    missing_message: str,
) -> HttpResponse:
    """
    Download a generated CleaningJobOutput.

    CleaningJobOutput is the authoritative source for generated files.
    """

    job, response = _get_current_job_response(
        request,
    )

    if response is not None:
        return response

    assert job is not None

    output = CleaningJobOutput.objects.filter(
        job=job,
        file_format=output_format,
    ).first()

    if output is None:
        messages.error(
            request,
            missing_message,
        )

        return redirect(
            "cleaner:upload",
        )

    file_field = output.file

    try:
        file_name = file_field.name or output.filename or ""
    except (AttributeError, ValueError):
        file_name = output.filename or ""

    if not file_name:
        logger.warning(
            "Output filename is missing for job %s (%s)",
            job.pk,
            output_format,
        )

        messages.error(
            request,
            missing_message,
        )

        return redirect(
            "cleaner:upload",
        )

    if not file_name.lower().endswith(
        expected_suffix.lower(),
    ):
        logger.warning(
            "Unexpected output type for job %s: %s",
            job.pk,
            file_name,
        )

        messages.error(
            request,
            missing_message,
        )

        return redirect(
            "cleaner:upload",
        )

    try:
        file_handle = file_field.open("rb")

    except (
        FileNotFoundError,
        OSError,
        ValueError,
    ):
        logger.warning(
            "Output file is unavailable for job %s: %s",
            job.pk,
            file_name,
        )

        messages.error(
            request,
            missing_message,
        )

        return redirect(
            "cleaner:upload",
        )

    response = FileResponse(
        file_handle,
        content_type=content_type,
    )

    download_name = Path(
        output.filename or file_name
    ).name

    response["Content-Disposition"] = (
        f'attachment; filename="{download_name}"'
    )

    return response


def _mark_job_failed(
    job: CleaningJob,
    error_message: str,
) -> None:
    """
    Persist a cleaning-job failure when pipeline execution fails.
    """

    try:
        job.status = CleaningJob.Status.FAILED
        job.error_message = error_message

        job.save(
            update_fields=[
                "status",
                "error_message",
                "updated_at",
            ],
        )

    except Exception:
        logger.exception(
            "Unable to persist failure state for cleaning job %s",
            job.pk,
        )