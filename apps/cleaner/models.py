from __future__ import annotations

from django.db import models


class CleaningJob(models.Model):

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    dataset = models.ForeignKey(
        "datasets.Dataset",
        on_delete=models.CASCADE,
        related_name="cleaning_jobs",
        null=True,
        blank=True,
    )

    original_file = models.FileField(
        upload_to="uploads/",
        blank=True,
        null=True,
    )

    # Legacy CSV output field.
    #
    # Kept for backwards compatibility with the current application
    # and existing database records. New code should use outputs.
    cleaned_file = models.FileField(
        upload_to="cleaned/",
        blank=True,
        null=True,
    )

    row_count = models.PositiveBigIntegerField(
        default=0,
    )

    issues_found = models.PositiveBigIntegerField(
        default=0,
    )

    issues_fixed = models.PositiveBigIntegerField(
        default=0,
    )

    rows_removed = models.PositiveBigIntegerField(
        default=0,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    error_message = models.TextField(
        blank=True,
        default="",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    completed_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(
                fields=["status", "-created_at"],
                name="cleaning_status_created_idx",
            ),
            models.Index(
                fields=["dataset", "-created_at"],
                name="cleaning_dataset_created_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"Cleaning Job #{self.id}"


class CleaningJobOutput(models.Model):
    """
    A generated file belonging to a cleaning job.

    One cleaning job can have multiple outputs, for example:

        csv  -> cleaned dataset
        xlsx -> cleaned Excel workbook
        pdf  -> cleaning report
    """

    class Format(models.TextChoices):
        CSV = "csv", "CSV"
        XLSX = "xlsx", "Excel"
        PDF = "pdf", "PDF"

    job = models.ForeignKey(
        CleaningJob,
        on_delete=models.CASCADE,
        related_name="outputs",
    )

    file = models.FileField(
        upload_to="cleaned/",
    )

    file_format = models.CharField(
        max_length=10,
        choices=Format.choices,
        db_index=True,
    )

    filename = models.CharField(
        max_length=255,
    )

    content_type = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["file_format", "id"]

        constraints = [
            models.UniqueConstraint(
                fields=["job", "file_format"],
                name="unique_cleaning_job_output_format",
            ),
        ]

        indexes = [
            models.Index(
                fields=["job", "file_format"],
                name="cleaning_output_job_format_idx",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"{self.file_format.upper()} output "
            f"for Cleaning Job #{self.job_id}"
        )


class CleaningFinding(models.Model):

    class FindingType(models.TextChoices):
        MISSING = "missing", "Missing Value"
        DUPLICATE = "duplicate", "Duplicate Row"
        INVALID = "invalid", "Invalid Value"
        FORMATTING = "formatting", "Formatting Issue"

    job = models.ForeignKey(
        CleaningJob,
        on_delete=models.CASCADE,
        related_name="findings",
    )

    finding_type = models.CharField(
        max_length=20,
        choices=FindingType.choices,
        db_index=True,
    )

    column_name = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    row_number = models.PositiveBigIntegerField(
        blank=True,
        null=True,
    )

    description = models.TextField()

    fixed = models.BooleanField(
        default=False,
        db_index=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["created_at", "id"]

        indexes = [
            models.Index(
                fields=["job", "finding_type"],
                name="finding_job_type_idx",
            ),
            models.Index(
                fields=["job", "fixed"],
                name="finding_job_fixed_idx",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"{self.get_finding_type_display()} "
            f"— Job #{self.job_id}"
        )