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
        upload_to="uploads/"
    )

    cleaned_file = models.FileField(
        upload_to="cleaned/",
        blank=True,
        null=True,
    )

    row_count = models.PositiveIntegerField(
        default=0
    )

    issues_found = models.PositiveIntegerField(
        default=0
    )

    issues_fixed = models.PositiveIntegerField(
        default=0
    )

    rows_removed = models.PositiveIntegerField(
        default=0
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    error_message = models.TextField(
        blank=True,
        default="",
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    completed_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"Cleaning Job #{self.id}"

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
    )

    column_name = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    row_number = models.PositiveIntegerField(
        blank=True,
        null=True,
    )

    description = models.TextField()

    fixed = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return (
            f"{self.get_finding_type_display()} "
            f"— Job #{self.job_id}"
        )