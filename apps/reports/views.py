from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from apps.cleaner.models import CleaningJob
from apps.reports.services import get_job_history, get_job_report


def history(request):
    jobs = get_job_history()

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

    context = get_job_report(job)

    return render(
        request,
        "reports/report.html",
        context,
    )
