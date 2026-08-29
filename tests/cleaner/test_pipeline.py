from __future__ import annotations

from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from apps.cleaner.models import (
    CleaningFinding,
    CleaningJob,
    CleaningJobOutput,
)
from apps.cleaner.services.pipeline import CleaningPipeline
from apps.datasets.models import Dataset
from openpyxl import Workbook

from pathlib import Path


@override_settings(
    MEDIA_ROOT="/tmp/datapilot-test-media"
)
class CleaningPipelineTests(TestCase):

    def _create_dataset(
        self,
        content: bytes = (
            b"name,age\n"
            b"Amani,20\n"
            b"John,\n"
            b"John,25\n"
        ),
        filename: str = "customers.csv",
    ) -> Dataset:
        uploaded_file = SimpleUploadedFile(
            filename,
            content,
            content_type="text/csv",
        )

        return Dataset.objects.create(
            name="Customers",
            original_file=uploaded_file,
        )

    def _create_job(
        self,
        dataset: Dataset,
    ) -> CleaningJob:
        return CleaningJob.objects.create(
            dataset=dataset,
            original_file=dataset.original_file,
        )

    def test_pipeline_completes_successfully(self):
        dataset = self._create_dataset()
        job = self._create_job(dataset)

        result = CleaningPipeline(job).run()

        job.refresh_from_db()
        dataset.refresh_from_db()

        self.assertEqual(
            job.status,
            CleaningJob.Status.COMPLETED,
        )

        self.assertEqual(
            dataset.status,
            Dataset.Status.CLEANED,
        )

        self.assertIsNotNone(
            job.completed_at,
        )

        self.assertIsNotNone(
            job.cleaned_file,
        )

        self.assertTrue(
            job.cleaned_file.name,
        )

        self.assertIn(
            "cleaned",
            job.cleaned_file.name,
        )

        self.assertIn(
            "cleaned_dataframe",
            result,
        )

    def test_pipeline_creates_all_standard_outputs(self):
        dataset = self._create_dataset()
        job = self._create_job(dataset)

        result = CleaningPipeline(job).run()

        outputs = CleaningJobOutput.objects.filter(
            job=job
        )

        self.assertEqual(
            outputs.count(),
            3,
        )

        formats = set(
            outputs.values_list(
                "file_format",
                flat=True,
            )
        )

        self.assertEqual(
            formats,
            {
                CleaningJobOutput.Format.CSV,
                CleaningJobOutput.Format.XLSX,
                CleaningJobOutput.Format.PDF,
            },
        )

        self.assertTrue(
            result["csv_filename"].endswith(
                ".csv"
            )
        )

        self.assertTrue(
            result["xlsx_filename"].endswith(
                ".xlsx"
            )
        )

        self.assertTrue(
            result["pdf_filename"].endswith(
                ".pdf"
            )
        )

    def test_pipeline_returns_statistics(self):
        dataset = self._create_dataset()
        job = self._create_job(dataset)

        result = CleaningPipeline(job).run()

        statistics = result["statistics"]

        self.assertIsInstance(
            statistics,
            dict,
        )

        self.assertEqual(
            statistics["original_rows"],
            3,
        )

        self.assertIn(
            "final_rows",
            statistics,
        )

        self.assertIn(
            "rows_removed",
            statistics,
        )

    def test_pipeline_creates_excel_output(self):
        dataset = self._create_dataset()
        job = self._create_job(dataset)

        CleaningPipeline(job).run()

        output = CleaningJobOutput.objects.get(
            job=job,
            file_format=CleaningJobOutput.Format.XLSX,
        )

        self.assertTrue(
            output.filename.endswith(
                ".xlsx"
            )
        )

        self.assertTrue(
            output.file.name.startswith(
                "cleaned/"
            )
        )

        self.assertEqual(
            output.content_type,
            (
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
        )

        self.assertTrue(
            Path(
                output.file.path
            ).exists()
        )

    def test_pipeline_persists_job_statistics(self):
        dataset = self._create_dataset()
        job = self._create_job(dataset)

        CleaningPipeline(job).run()

        job.refresh_from_db()

        self.assertEqual(
            job.row_count,
            3,
        )

        self.assertGreaterEqual(
            job.issues_found,
            1,
        )

        self.assertGreaterEqual(
            job.issues_fixed,
            1,
        )

        self.assertGreaterEqual(
            job.rows_removed,
            0,
        )

    def test_pipeline_persists_dataset_cleaned_file(self):
        dataset = self._create_dataset()
        job = self._create_job(dataset)

        CleaningPipeline(job).run()

        dataset.refresh_from_db()

        self.assertTrue(
            dataset.cleaned_file.name,
        )

        self.assertIn(
            "cleaned",
            dataset.cleaned_file.name,
        )

    def test_pipeline_creates_cleaning_findings(self):
        dataset = self._create_dataset()
        job = self._create_job(dataset)

        CleaningPipeline(job).run()

        findings = CleaningFinding.objects.filter(
            job=job
        )

        self.assertGreaterEqual(
            findings.count(),
            1,
        )

        finding_types = set(
            findings.values_list(
                "finding_type",
                flat=True,
            )
        )

        self.assertIn(
            CleaningFinding.FindingType.MISSING,
            finding_types,
        )

    def test_pipeline_fails_without_original_file(self):
        job = CleaningJob.objects.create()

        with self.assertRaisesMessage(
            ValueError,
            "Cleaning job does not have an original file.",
        ):
            CleaningPipeline(job).run()

        job.refresh_from_db()

        self.assertEqual(
            job.status,
            CleaningJob.Status.FAILED,
        )

        self.assertTrue(
            job.error_message,
        )

    def test_pipeline_marks_dataset_failed_on_error(self):
        dataset = self._create_dataset()

        job = CleaningJob.objects.create(
            dataset=dataset,
        )

        with self.assertRaisesMessage(
            ValueError,
            "Cleaning job does not have an original file.",
        ):
            CleaningPipeline(job).run()

        job.refresh_from_db()
        dataset.refresh_from_db()

        self.assertEqual(
            job.status,
            CleaningJob.Status.FAILED,
        )

        self.assertEqual(
            dataset.status,
            Dataset.Status.FAILED,
        )

    def test_pipeline_accepts_excel_workbook(self):
        workbook = Workbook()

        worksheet = workbook.active
        worksheet.title = "Customers"

        worksheet.append(
            ["name", "age"]
        )

        worksheet.append(
            ["Amani", 20]
        )

        worksheet.append(
            ["John", None]
        )

        worksheet.append(
            ["John", 25]
        )

        buffer = BytesIO()

        workbook.save(
            buffer
        )

        buffer.seek(0)

        uploaded_file = SimpleUploadedFile(
            "customers.xlsx",
            buffer.getvalue(),
            content_type=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
        )

        dataset = Dataset.objects.create(
            name="Excel Customers",
            original_file=uploaded_file,
        )

        job = CleaningJob.objects.create(
            dataset=dataset,
            original_file=dataset.original_file,
        )

        result = CleaningPipeline(job).run()

        job.refresh_from_db()
        dataset.refresh_from_db()

        self.assertEqual(
            job.status,
            CleaningJob.Status.COMPLETED,
        )

        self.assertEqual(
            dataset.status,
            Dataset.Status.CLEANED,
        )

        self.assertEqual(
            result["statistics"]["original_rows"],
            3,
        )

        self.assertTrue(
            job.cleaned_file.name
        )

        self.assertTrue(
            dataset.cleaned_file.name
        )

        self.assertIn(
            "cleaned",
            job.cleaned_file.name,
        )