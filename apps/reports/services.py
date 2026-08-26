from apps.cleaner.models import CleaningJob


def get_job_history(limit=None):

    queryset = (
        CleaningJob.objects
        .order_by("-created_at")
    )

    if limit:
        queryset = queryset[:limit]

    return queryset


def get_job_report(job):

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
    }