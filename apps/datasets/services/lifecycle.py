from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from apps.datasets.models import Dataset


class DatasetLifecycleError(ValueError):
    """Raised when an invalid dataset state transition is requested."""


class DatasetLifecycleService:
    """
    Controls valid Dataset state transitions.

    State flow:

        uploaded
            ↓
        processing
         ↙      ↘
    failed     cleaned
         ↑
         └── retry → processing
    """

    _TRANSITIONS: dict[str, set[str]] = {
        Dataset.Status.UPLOADED: {
            Dataset.Status.PROCESSING,
        },
        Dataset.Status.PROCESSING: {
            Dataset.Status.UPLOADED,
            Dataset.Status.CLEANED,
            Dataset.Status.FAILED,
        },
        Dataset.Status.CLEANED: {
            Dataset.Status.PROCESSING,
        },
        Dataset.Status.FAILED: {
            Dataset.Status.PROCESSING,
        },
    }

    @classmethod
    def can_transition(
        cls,
        current: str,
        target: str,
    ) -> bool:
        """Return whether a state transition is allowed."""

        if current == target:
            return True

        return target in cls._TRANSITIONS.get(
            current,
            set(),
        )

    @classmethod
    @transaction.atomic
    def transition(
        cls,
        dataset: Dataset,
        target: str,
        *,
        error_message: str | None = None,
    ) -> Dataset:
        """
        Transition a dataset to a new lifecycle state.

        Timestamp and error metadata are maintained consistently.
        """

        current = dataset.status

        if not cls.can_transition(
            current,
            target,
        ):
            raise DatasetLifecycleError(
                f"Invalid dataset state transition: "
                f"{current} -> {target}"
            )

        now = timezone.now()

        dataset.status = target

        update_fields = [
            "status",
            "updated_at",
        ]

        if target == Dataset.Status.PROCESSING:
            dataset.processing_started_at = now
            dataset.completed_at = None
            dataset.error_message = ""

            update_fields.extend(
                [
                    "processing_started_at",
                    "completed_at",
                    "error_message",
                ]
            )

        elif target in {
            Dataset.Status.UPLOADED,
            Dataset.Status.CLEANED,
        }:
            dataset.completed_at = now
            dataset.error_message = ""

            update_fields.extend(
                [
                    "completed_at",
                    "error_message",
                ]
            )

        elif target == Dataset.Status.FAILED:
            dataset.error_message = (
                error_message or ""
            )

            update_fields.append(
                "error_message"
            )

        dataset.save(
            update_fields=update_fields
        )

        return dataset

    @classmethod
    def start_processing(
        cls,
        dataset: Dataset,
    ) -> Dataset:
        return cls.transition(
            dataset,
            Dataset.Status.PROCESSING,
        )

    @classmethod
    def mark_uploaded(
        cls,
        dataset: Dataset,
    ) -> Dataset:
        return cls.transition(
            dataset,
            Dataset.Status.UPLOADED,
        )

    @classmethod
    def mark_cleaned(
        cls,
        dataset: Dataset,
    ) -> Dataset:
        return cls.transition(
            dataset,
            Dataset.Status.CLEANED,
        )

    @classmethod
    def mark_failed(
        cls,
        dataset: Dataset,
        error_message: str,
    ) -> Dataset:
        return cls.transition(
            dataset,
            Dataset.Status.FAILED,
            error_message=error_message,
        )