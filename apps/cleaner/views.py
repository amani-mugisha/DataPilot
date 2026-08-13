"""
Views for the cleaner app: upload -> scan -> clean -> download.

State between steps is kept in the session (dataset_id, cleaning_job_id,
file paths) since a single browser session drives one job through the
whole flow before moving to the next upload.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import pandas as pd
from django.conf import settings
from django.contrib import messages
from django.http import FileResponse, HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from apps.cleaner.models import CleaningJob
from apps.cleaner.services.cleaner import clean_dataframe
from apps.cleaner.services.pdf_report import generate_pdf_report
from apps.datasets.models import Dataset
from apps.datasets.services import analyze_dataset

logger = logging.getLogger(__name__)


def upload(request: HttpRequest) -> HttpResponse:
    """Accept a CSV upload, scan it, and show the scan-results page."""
    if request.method != "POST":
        return render(request, "cleaner/upload.html")

    uploaded_file = request.FILES.get("file")

    error = _validate_upload(uploaded_file)
    if error:
        messages.error(request, error)
        return render(request, "cleaner/upload.html")

    try:
        df = pd.read_csv(uploaded_file)
    except Exception as exc:
        logger.warning("Failed to parse uploaded CSV '%s': %s", uploaded_file.name, exc)
        messages.error(request, f"Could not read this CSV file: {exc}")
        return render(request, "cleaner/upload.html")

    scan = _scan_dataframe(df)

    dataset = Dataset.objects.create(
        name=uploaded_file.name,
        original_file=uploaded_file,
        file_size=uploaded_file.size,
        row_count=scan["rows"],
        column_count=scan["columns"],
        status=Dataset.Status.UPLOADED,
    )
    analyze_dataset(dataset)

    job = CleaningJob.objects.create(
        dataset=dataset,
        original_file=dataset.original_file,
        row_count=scan["rows"],
        status=CleaningJob.Status.PENDING,
    )

    request.session["dataset_id"] = dataset.id
    request.session["cleaning_job_id"] = job.id
    request.session["uploaded_file_path"] = dataset.original_file.path
    request.session["original_filename"] = uploaded_file.name

    context = {**scan, "dataset": dataset, "job": job}
    return render(request, "cleaner/results.html", context)


def clean_file(request: HttpRequest) -> HttpResponse:
    """Run the cleaning pipeline on the session's pending job and show results."""
    if request.method != "POST":
        return redirect("cleaner:upload")

    session_data, error = _get_session_job_data(request)
    if error:
        messages.error(request, error)
        return redirect("cleaner:upload")

    try:
        job = CleaningJob.objects.select_related("dataset").get(id=session_data["job_id"])
    except CleaningJob.DoesNotExist:
        messages.error(request, "The cleaning job could not be found.")
        return redirect("cleaner:upload")

    try:
        return _run_cleaning_pipeline(request, job, session_data)
    except Exception as exc:
        logger.exception("Cleaning job %s failed", job.id)
        _mark_job_failed(job, str(exc))
        messages.error(request, f"Could not clean this CSV file: {exc}")
        return redirect("cleaner:upload")


def download_csv(request: HttpRequest) -> HttpResponse:
    """Download the cleaned CSV produced by the most recent clean_file() run."""
    return _download_session_file(
        request,
        session_key="cleaned_csv_path",
        content_type="text/csv",
        missing_message="The cleaned CSV file is no longer available.",
    )


def download_pdf(request: HttpRequest) -> HttpResponse:
    """Download the PDF report produced by the most recent clean_file() run."""
    return _download_session_file(
        request,
        session_key="cleaned_pdf_path",
        content_type="application/pdf",
        missing_message="The PDF report is no longer available.",
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _validate_upload(uploaded_file) -> str | None:
    """Return an error message if the upload is invalid, else None."""
    if not uploaded_file:
        return "Please choose a CSV file."
    if not uploaded_file.name.lower().endswith(".csv"):
        return "Only CSV files are accepted."
    return None


def _scan_dataframe(df: pd.DataFrame) -> dict:
    """Cheap, read-only stats shown on the scan-results page before cleaning runs."""
    return {
        "rows": len(df),
        "columns": len(df.columns),
        "missing_values": int(df.isna().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
    }


def _get_session_job_data(request: HttpRequest) -> tuple[dict, str | None]:
    """Pull the pending job's session state, or an error message if incomplete."""
    file_path = request.session.get("uploaded_file_path")
    job_id = request.session.get("cleaning_job_id")

    if not file_path:
        return {}, "No uploaded CSV file was found."
    if not job_id:
        return {}, "No cleaning job was found."

    return {
        "file_path": file_path,
        "job_id": job_id,
        "original_filename": request.session.get("original_filename", "uploaded.csv"),
    }, None


def _run_cleaning_pipeline(request: HttpRequest, job: CleaningJob, session_data: dict) -> HttpResponse:
    """Execute clean -> save outputs -> update records -> render results."""
    _mark_job_processing(job)

    df = pd.read_csv(session_data["file_path"])
    cleaned_df, statistics = clean_dataframe(df)

    cleaned_dir = Path(settings.MEDIA_ROOT) / "cleaned"
    cleaned_dir.mkdir(parents=True, exist_ok=True)

    base_name = os.path.splitext(session_data["original_filename"])[0]
    csv_filename = f"{base_name}_cleaned.csv"
    pdf_filename = f"{base_name}_cleaning_report.pdf"
    csv_path = cleaned_dir / csv_filename
    pdf_path = cleaned_dir / pdf_filename

    cleaned_df.to_csv(csv_path, index=False)

    pdf_buffer = generate_pdf_report(session_data["original_filename"], cleaned_df)
    pdf_path.write_bytes(pdf_buffer.getvalue())

    _mark_job_complete(job, statistics, csv_filename)

    request.session["cleaned_csv_path"] = str(csv_path)
    request.session["cleaned_pdf_path"] = str(pdf_path)
    request.session["statistics"] = statistics

    context = {
        "statistics": statistics,
        "csv_filename": csv_filename,
        "pdf_filename": pdf_filename,
        "job": job,
        "dataset": job.dataset,
    }
    return render(request, "cleaner/clean_results.html", context)


def _mark_job_processing(job: CleaningJob) -> None:
    job.status = CleaningJob.Status.PROCESSING
    job.save(update_fields=["status", "updated_at"])

    if job.dataset:
        job.dataset.status = Dataset.Status.PROCESSING
        job.dataset.save(update_fields=["status", "updated_at"])


def _mark_job_complete(job: CleaningJob, statistics: dict, csv_filename: str) -> None:
    fixed_issue_count = statistics["missing_values"] + statistics["duplicates_removed"]

    job.row_count = statistics["original_rows"]
    job.issues_found = fixed_issue_count
    job.issues_fixed = fixed_issue_count
    job.rows_removed = statistics["rows_removed"]
    job.cleaned_file.name = f"cleaned/{csv_filename}"
    job.status = CleaningJob.Status.COMPLETED
    job.completed_at = timezone.now()
    job.save(update_fields=[
        "cleaned_file", "row_count", "issues_found", "issues_fixed",
        "rows_removed", "status", "completed_at", "updated_at",
    ])

    if job.dataset:
        job.dataset.cleaned_file.name = f"cleaned/{csv_filename}"
        job.dataset.status = Dataset.Status.CLEANED
        job.dataset.save(update_fields=["cleaned_file", "status", "updated_at"])


def _mark_job_failed(job: CleaningJob, error_message: str) -> None:
    job.status = CleaningJob.Status.FAILED
    job.error_message = error_message
    job.save(update_fields=["status", "error_message", "updated_at"])

    if job.dataset:
        job.dataset.status = Dataset.Status.FAILED
        job.dataset.save(update_fields=["status", "updated_at"])


def _download_session_file(
    request: HttpRequest, *, session_key: str, content_type: str, missing_message: str
) -> HttpResponse:
    file_path = request.session.get(session_key)

    if not file_path or not os.path.exists(file_path):
        messages.error(request, missing_message)
        return redirect("cleaner:upload")

    return FileResponse(
        open(file_path, "rb"),
        as_attachment=True,
        filename=os.path.basename(file_path),
        content_type=content_type,
    )