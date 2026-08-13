from django.urls import path

from . import views


app_name = "cleaner"


urlpatterns = [
    path(
        "",
        views.upload,
        name="upload",
    ),

    path(
        "clean/",
        views.clean_file,
        name="clean",
    ),

    path(
        "download/csv/",
        views.download_csv,
        name="download_csv",
    ),

    path(
        "download/pdf/",
        views.download_pdf,
        name="download_pdf",
    ),
]