from django.core.paginator import Paginator
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.cleaner.models import CleaningJob


def history(request):
    jobs = (
        CleaningJob.objects
        .select_related("dataset")
        .prefetch_related("findings")
        .order_by("-created_at")
    )

    paginator = Paginator(jobs, 20)
    page_number = request.GET.get("page")
    jobs_page = paginator.get_page(page_number)

    return render(
        request,
        "reports/history.html",
        {
            "jobs": jobs_page,
        },
    )


def report(request, job_id):
    job = get_object_or_404(
        CleaningJob.objects.select_related("dataset"),
        id=job_id,
    )

    summary = {
    "row_count": job.row_count,
    "issues_found": job.issues_found,
    "issues_fixed": job.issues_fixed,
    "rows_removed": job.rows_removed,
    }

    findings = job.findings.all()

    download_url = (
        job.cleaned_file.url
        if job.cleaned_file
        else None
    )

    context = {
        "job": job,
        "summary": summary,
        "findings": findings,
        "download_url": download_url,
    }

    return render(
        request,
        "reports/report.html",
        context,
    )