from __future__ import annotations

from django.core.validators import MinValueValidator
from django.db import models


class Dataset(models.Model):

    class Status(models.TextChoices):
        UPLOADED = "uploaded", "Uploaded"
        PROCESSING = "processing", "Processing"
        CLEANED = "cleaned", "Cleaned"
        FAILED = "failed", "Failed"

    name = models.CharField(
        max_length=255,
    )

    original_file = models.FileField(
        upload_to="datasets/original/",
    )

    cleaned_file = models.FileField(
        upload_to="datasets/cleaned/",
        blank=True,
        null=True,
    )

    original_filename = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    file_type = models.CharField(
        max_length=100,
        blank=True,
        default="",
        db_index=True,
    )

    mime_type = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    file_size = models.PositiveBigIntegerField(
        default=0,
    )

    checksum = models.CharField(
        max_length=64,
        blank=True,
        default="",
        db_index=True,
    )

    row_count = models.PositiveBigIntegerField(
        default=0,
    )

    column_count = models.PositiveIntegerField(
        default=0,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.UPLOADED,
        db_index=True,
    )

    error_message = models.TextField(
        blank=True,
        default="",
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    processing_started_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    completed_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["-uploaded_at"]

        indexes = [
            models.Index(
                fields=["status", "-uploaded_at"],
                name="dataset_status_uploaded_idx",
            ),
            models.Index(
                fields=["file_type"],
                name="dataset_file_type_idx",
            ),
            models.Index(
                fields=["checksum"],
                name="dataset_checksum_idx",
            ),
        ]

        constraints = [
            models.CheckConstraint(
                condition=models.Q(file_size__gte=0),
                name="dataset_file_size_nonnegative",
            ),
            models.CheckConstraint(
                condition=models.Q(row_count__gte=0),
                name="dataset_row_count_nonnegative",
            ),
            models.CheckConstraint(
                condition=models.Q(column_count__gte=0),
                name="dataset_column_count_nonnegative",
            ),
        ]

    def __str__(self) -> str:
        return self.name


class DatasetColumn(models.Model):

    dataset = models.ForeignKey(
        Dataset,
        on_delete=models.CASCADE,
        related_name="columns",
    )

    name = models.CharField(
        max_length=255,
    )

    data_type = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )

    missing_count = models.PositiveBigIntegerField(
        default=0,
    )

    unique_count = models.PositiveBigIntegerField(
        default=0,
    )

    position = models.PositiveIntegerField(
        default=0,
    )

    class Meta:
        ordering = ["position", "id"]

        constraints = [
            models.UniqueConstraint(
                fields=["dataset", "name"],
                name="unique_dataset_column_name",
            ),
            models.CheckConstraint(
                condition=models.Q(missing_count__gte=0),
                name="dataset_column_missing_nonnegative",
            ),
            models.CheckConstraint(
                condition=models.Q(unique_count__gte=0),
                name="dataset_column_unique_nonnegative",
            ),
        ]

        indexes = [
            models.Index(
                fields=["dataset", "position"],
                name="dataset_column_position_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.dataset.name} - {self.name}"