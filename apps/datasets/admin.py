from django.contrib import admin

from .models import Dataset, DatasetColumn


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "row_count",
        "column_count",
        "status",
        "uploaded_at",
    )

    list_filter = (
        "status",
        "uploaded_at",
    )

    search_fields = (
        "name",
    )


@admin.register(DatasetColumn)
class DatasetColumnAdmin(admin.ModelAdmin):
    list_display = (
        "dataset",
        "name",
        "data_type",
        "missing_count",
        "unique_count",
    )

    search_fields = (
        "name",
        "dataset__name",
    )