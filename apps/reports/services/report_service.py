from __future__ import annotations

from django.db.models import Prefetch, QuerySet

from apps.cleaner.models import (
    CleaningFinding,
    CleaningJob,
    CleaningJobOutput,
)


def get_job_history(
    limit: int | None = None,
) -> QuerySet[CleaningJob]:
    """
    Return cleaning jobs ordered from newest to oldest.

    Dataset metadata and generated outputs are loaded efficiently
    because the history page displays information from both
    relationships.

    Args:
        limit:
            Optional maximum number of jobs to return.

    Returns:
        QuerySet of CleaningJob objects ordered newest first.
    """

    output_queryset = CleaningJobOutput.objects.order_by(
        "file_format",
        "id",
    )

    queryset = (
        CleaningJob.objects
        .select_related("dataset")
        .prefetch_related(
            Prefetch(
                "outputs",
                queryset=output_queryset,
            ),
        )
        .order_by(
            "-created_at",
            "-id",
        )
    )

    if limit is not None:
        queryset = queryset[:limit]

    return queryset


def get_job_report(
    job: CleaningJob,
) -> dict:
    """
    Build the complete context required by the cleaning report page.

    CleaningJobOutput is the authoritative source for generated
    cleaning outputs.

    The legacy ``download_url`` field is retained as a compatibility
    convenience and points to the generated CSV output when one
    exists. New code should use the report download endpoint and
    ``outputs`` instead.
    """

    findings = (
        CleaningFinding.objects
        .filter(job=job)
        .order_by(
            "created_at",
            "id",
        )
    )

    outputs = list(
        job.outputs.all()
    )

    outputs_by_format = {
        output.file_format: output
        for output in outputs
    }

    csv_output = outputs_by_format.get(
        CleaningJobOutput.Format.CSV,
    )

    download_url = (
        csv_output.file.url
        if csv_output is not None
        else None
    )

    return {
        "job": job,
        "dataset": job.dataset,
        "findings": findings,
        "outputs": outputs,
        "outputs_by_format": outputs_by_format,
        "download_url": download_url,
        "summary": {
            "row_count": job.row_count,
            "issues_found": job.issues_found,
            "issues_fixed": job.issues_fixed,
            "rows_removed": job.rows_removed,
        },
    }