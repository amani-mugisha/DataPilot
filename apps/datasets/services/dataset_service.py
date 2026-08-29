from __future__ import annotations

import hashlib
from pathlib import Path

from django.core.files.base import File
from django.db import transaction

from apps.datasets.models import Dataset
from apps.importer.services import ImportService


class DatasetService:
    """
    Application service responsible for creating and preparing datasets.

    Responsibilities:

        uploaded file
            ↓
        Dataset record
            ↓
        importer validation
            ↓
        dataset analysis

    File parsing remains the responsibility of ImportService.
    Dataset metadata remains the responsibility of the analyzer.
    """

    def __init__(self) -> None:
        self.importer = ImportService()

    @transaction.atomic
    def create(
        self,
        *,
        name: str,
        uploaded_file: File,
    ) -> Dataset:
        """
        Create a Dataset from an uploaded file.

        The uploaded file stream is always reset to position 0
        before this method returns or raises.
        """

        if not name or not name.strip():
            raise ValueError(
                "Dataset name cannot be empty."
            )

        if uploaded_file is None:
            raise ValueError(
                "Dataset file is required."
            )

        try:
            filename = Path(
                uploaded_file.name
            ).name

            if not filename:
                raise ValueError(
                    "Dataset file must have a filename."
                )

            file_size = self._get_file_size(
                uploaded_file
            )

            detected = self.importer.validate(
                file_path=uploaded_file,
                filename=filename,
                file_size=file_size,
                mime_type=getattr(
                    uploaded_file,
                    "content_type",
                    None,
                ),
            )

            checksum = self._calculate_checksum(
                uploaded_file
            )

            dataset = Dataset.objects.create(
                name=name.strip(),
                original_file=uploaded_file,
                original_filename=filename,
                file_type=detected.format,
                mime_type=(
                    detected.mime_type or ""
                ),
                file_size=file_size,
                checksum=checksum,
                status=Dataset.Status.UPLOADED,
            )

            return dataset

        finally:
            uploaded_file.seek(0)

    def validate_file(
        self,
        uploaded_file: File,
    ):
        """
        Validate an uploaded dataset without creating a record.

        The uploaded file stream is reset to position 0 before
        this method returns or raises.
        """

        if uploaded_file is None:
            raise ValueError(
                "Dataset file is required."
            )

        try:
            filename = Path(
                uploaded_file.name
            ).name

            if not filename:
                raise ValueError(
                    "Dataset file must have a filename."
                )

            return self.importer.validate(
                file_path=uploaded_file,
                filename=filename,
                file_size=self._get_file_size(
                    uploaded_file
                ),
                mime_type=getattr(
                    uploaded_file,
                    "content_type",
                    None,
                ),
            )

        finally:
            uploaded_file.seek(0)

    @staticmethod
    def _get_file_size(
        uploaded_file: File,
    ) -> int:
        """
        Return the uploaded file size without relying
        on filesystem paths.
        """

        size = getattr(
            uploaded_file,
            "size",
            None,
        )

        if size is None:
            raise ValueError(
                "Unable to determine uploaded file size."
            )

        return int(size)

    @staticmethod
    def _calculate_checksum(
        uploaded_file: File,
    ) -> str:
        """
        Calculate a SHA-256 checksum for the uploaded file.

        The stream is reset before hashing and after hashing.
        """

        hasher = hashlib.sha256()

        try:
            uploaded_file.seek(0)

            while True:
                chunk = uploaded_file.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                hasher.update(chunk)

        finally:
            uploaded_file.seek(0)

        return hasher.hexdigest()