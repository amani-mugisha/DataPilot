from django.urls import path

from . import views


app_name = "reports"


urlpatterns = [
    path(
        "",
        views.history,
        name="history",
    ),

    path(
        "<int:job_id>/",
        views.report,
        name="report",
    ),

    path(
        "<int:job_id>/download/<str:file_format>/",
        views.download,
        name="download",
    ),
]
