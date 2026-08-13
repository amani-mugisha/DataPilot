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
]