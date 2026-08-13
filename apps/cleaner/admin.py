from django.contrib import admin

from .models import CleaningFinding, CleaningJob


@admin.register(CleaningJob)
class CleaningJobAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "original_file",
        "status",
        "row_count",
        "issues_found",
        "issues_fixed",
        "rows_removed",
        "created_at",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "original_file",
        "cleaned_file",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "completed_at",
    )


@admin.register(CleaningFinding)
class CleaningFindingAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "job",
        "finding_type",
        "column_name",
        "row_number",
        "fixed",
        "created_at",
    )

    list_filter = (
        "finding_type",
        "fixed",
        "created_at",
    )

    search_fields = (
        "column_name",
        "description",
    )

    readonly_fields = (
        "created_at",
    )