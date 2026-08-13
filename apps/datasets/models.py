from django.db import models


class Dataset(models.Model):
    class Status(models.TextChoices):
        UPLOADED = "uploaded", "Uploaded"
        PROCESSING = "processing", "Processing"
        CLEANED = "cleaned", "Cleaned"
        FAILED = "failed", "Failed"

    name = models.CharField(max_length=255)

    original_file = models.FileField(
        upload_to="datasets/original/"
    )

    cleaned_file = models.FileField(
        upload_to="datasets/cleaned/",
        blank=True,
        null=True,
    )

    file_size = models.PositiveBigIntegerField(default=0)

    row_count = models.PositiveIntegerField(default=0)

    column_count = models.PositiveIntegerField(default=0)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.UPLOADED,
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.name


class DatasetColumn(models.Model):
    dataset = models.ForeignKey(
        Dataset,
        on_delete=models.CASCADE,
        related_name="columns",
    )

    name = models.CharField(max_length=255)

    data_type = models.CharField(
        max_length=100,
        blank=True,
    )

    missing_count = models.PositiveIntegerField(default=0)

    unique_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.dataset.name} - {self.name}"