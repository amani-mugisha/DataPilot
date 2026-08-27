from apps.cleaner.models import CleaningJob


def get_job_history(limit=None):
    """
    Return cleaning jobs ordered from newest to oldest.

    Args:
        limit: Optional maximum number of jobs to return.
    """
    queryset = (
        CleaningJob.objects
        .select_related("dataset")
        .prefetch_related("findings")
        .order_by("-created_at")
    )

    if limit is not None:
        queryset = queryset[:limit]

    return queryset


def get_job_report(job):
    """
    Build the data required by the report detail page.
    """
    findings = job.findings.all()

    return {
        "job": job,
        "findings": findings,
        "summary": {
            "row_count": job.row_count,
            "issues_found": job.issues_found,
            "issues_fixed": job.issues_fixed,
            "rows_removed": job.rows_removed,
        },
        "download_url": (
            job.cleaned_file.url
            if job.cleaned_file
            else None
        ),
    }
