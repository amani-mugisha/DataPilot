from __future__ import annotations

from dataclasses import dataclass

from django.core.files.base import File
from django.db import transaction

from apps.cleaner.models import CleaningJob
from apps.datasets.models import Dataset
from apps.datasets.services.analyzer import analyze_dataset
from apps.datasets.services.dataset_service import DatasetService
from apps.importer.results import ImportResult
from apps.importer.services import ImportService


@dataclass(frozen=True)
class DatasetIngestionResult:
    """
    Result of successfully ingesting a dataset.
    """

    dataset: Dataset
    cleaning_job: CleaningJob
    import_result: ImportResult


class DatasetIngestionService:
    """
    Orchestrates the complete dataset ingestion workflow.

    Workflow:

        uploaded file
            ↓
        dataset persistence
            ↓
        import
            ↓
        analysis
            ↓
        cleaning job creation

    A dataset that fails after persistence remains in the database
    with FAILED status and an error message.
    """

    def __init__(
        self,
        *,
        dataset_service: DatasetService | None = None,
        importer: ImportService | None = None,
    ) -> None:
        self.dataset_service = (
            dataset_service
            if dataset_service is not None
            else DatasetService()
        )

        self.importer = (
            importer
            if importer is not None
            else ImportService()
        )

    def ingest(
        self,
        *,
        name: str,
        uploaded_file: File,
    ) -> DatasetIngestionResult:
        """
        Persist and process an uploaded dataset.

        The Dataset record is deliberately created outside the
        processing transaction so failures can be persisted as
        Dataset.Status.FAILED.
        """

        if uploaded_file is None:
            raise ValueError(
                "Dataset file is required."
            )

        dataset = self.dataset_service.create(
            name=name,
            uploaded_file=uploaded_file,
        )

        try:
            with transaction.atomic():
                import_result = self.importer.read(
                    file_path=dataset.original_file.path,
                    filename=dataset.original_filename,
                    mime_type=dataset.mime_type or None,
                    file_size=dataset.file_size,
                )

                analyze_dataset(
                    dataset,
                    import_result.dataframe,
                )

                dataset.refresh_from_db()

                cleaning_job = CleaningJob.objects.create(
                    dataset=dataset,
                    original_file=dataset.original_file,
                    row_count=dataset.row_count,
                    status=CleaningJob.Status.PENDING,
                )

        except Exception as exc:
            self._mark_failed(
                dataset,
                str(exc),
            )
            raise

        return DatasetIngestionResult(
            dataset=dataset,
            cleaning_job=cleaning_job,
            import_result=import_result,
        )

    @staticmethod
    def _mark_failed(
        dataset: Dataset,
        error_message: str,
    ) -> None:
        """
        Persist a terminal dataset failure.

        This deliberately runs outside the processing transaction.
        """

        dataset.status = Dataset.Status.FAILED
        dataset.error_message = error_message

        dataset.save(
            update_fields=[
                "status",
                "error_message",
                "updated_at",
            ]
        )