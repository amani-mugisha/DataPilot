from __future__ import annotations

import logging
from pathlib import Path

from django.contrib import messages
from django.core.paginator import Paginator
from django.http import (
    FileResponse,
    HttpRequest,
    HttpResponse,
)
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.views.decorators.http import require_GET

from apps.cleaner.models import (
    CleaningJob,
    CleaningJobOutput,
)

from apps.reports.services import (
    get_job_history,
    get_job_report,
)


logger = logging.getLogger(__name__)


HISTORY_PAGE_SIZE = 20


DOWNLOAD_TYPES = {
    CleaningJobOutput.Format.CSV: (
        "text/csv",
        ".csv",
    ),
    CleaningJobOutput.Format.XLSX: (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xlsx",
    ),
    CleaningJobOutput.Format.PDF: (
        "application/pdf",
        ".pdf",
    ),
}


def history(
    request: HttpRequest,
) -> HttpResponse:
    """
    Display previous cleaning jobs with pagination.

    The history page intentionally paginates at the view layer
    rather than changing the service contract. The service remains
    reusable by other application components that may need the
    complete QuerySet.
    """

    queryset = get_job_history()

    paginator = Paginator(
        queryset,
        HISTORY_PAGE_SIZE,
    )

    page_number = request.GET.get(
        "page",
        1,
    )

    jobs = paginator.get_page(
        page_number,
    )

    return render(
        request,
        "reports/history.html",
        {
            "jobs": jobs,
        },
    )


def report(
    request: HttpRequest,
    job_id: int,
) -> HttpResponse:
    """
    Display the complete report for a cleaning job.
    """

    job = get_object_or_404(
        CleaningJob.objects
        .select_related("dataset")
        .prefetch_related(
            "outputs",
            "findings",
        ),
        id=job_id,
    )

    context = get_job_report(
        job,
    )

    return render(
        request,
        "reports/report.html",
        context,
    )


@require_GET
def download(
    request: HttpRequest,
    job_id: int,
    file_format: str,
) -> HttpResponse:
    """
    Download a generated output belonging to a specific
    cleaning job.

    CleaningJobOutput is the authoritative source for generated
    files.

    The requested format must:

    1. Be supported by DataPilot.
    2. Belong to the requested cleaning job.
    3. Have a valid filename.
    4. Have the expected file extension.
    5. Exist on the configured storage backend.
    """

    file_format = file_format.lower()

    if file_format not in DOWNLOAD_TYPES:
        messages.error(
            request,
            "That file format is not available.",
        )

        return redirect(
            "reports:report",
            job_id=job_id,
        )

    job = get_object_or_404(
        CleaningJob,
        id=job_id,
    )

    output = get_object_or_404(
        CleaningJobOutput,
        job=job,
        file_format=file_format,
    )

    content_type, expected_suffix = (
        DOWNLOAD_TYPES[file_format]
    )

    file_name = (
        output.filename
        or output.file.name
        or ""
    )

    if not file_name:
        logger.warning(
            "Missing filename for report output %s",
            output.pk,
        )

        messages.error(
            request,
            "The requested file is not available.",
        )

        return redirect(
            "reports:report",
            job_id=job_id,
        )

    if not file_name.lower().endswith(
        expected_suffix,
    ):
        logger.warning(
            "Invalid filename for output %s: %s",
            output.pk,
            file_name,
        )

        messages.error(
            request,
            "The requested file is not available.",
        )

        return redirect(
            "reports:report",
            job_id=job_id,
        )

    try:
        file_handle = output.file.open(
            "rb",
        )

    except (
        FileNotFoundError,
        OSError,
        ValueError,
    ):
        logger.warning(
            "Output file unavailable for output %s",
            output.pk,
        )

        messages.error(
            request,
            "The requested file is no longer available.",
        )

        return redirect(
            "reports:report",
            job_id=job_id,
        )

    download_name = Path(
        file_name,
    ).name

    response = FileResponse(
        file_handle,
        content_type=content_type,
    )

    response["Content-Disposition"] = (
        f'attachment; filename="{download_name}"'
    )

    return response