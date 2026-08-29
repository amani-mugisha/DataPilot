from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pandas as pd
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.cleaner.models import (
    CleaningJob,
    CleaningJobOutput,
)
from apps.cleaner.views import _get_session_job_data, _scan_dataframe
from apps.datasets.models import Dataset


class CleanerViewTests(TestCase):

    def _create_dataset(
        self,
        filename: str = "customers.csv",
    ) -> Dataset:
        uploaded_file = SimpleUploadedFile(
            filename,
            (
                b"name,age,city\n"
                b"Amani,20,Kigali\n"
                b"John,25,Butare\n"
            ),
            content_type="text/csv",
        )

        return Dataset.objects.create(
            name=filename,
            original_file=uploaded_file,
        )

    def _create_job(
        self,
        dataset: Dataset | None = None,
    ) -> CleaningJob:
        return CleaningJob.objects.create(
            dataset=dataset,
            original_file=(
                dataset.original_file
                if dataset
                else None
            ),
        )

    def _set_workflow_session(
        self,
        dataset: Dataset,
        job: CleaningJob,
    ) -> None:
        session = self.client.session

        session["dataset_id"] = dataset.pk
        session["cleaning_job_id"] = job.pk

        session.save()

    def test_upload_get_renders_upload_page(self):
        response = self.client.get(
            reverse("cleaner:upload"),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "cleaner/upload.html",
        )

    def test_upload_without_file_renders_error(self):
        response = self.client.post(
            reverse("cleaner:upload"),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        messages = list(
            response.context["messages"]
        )

        self.assertTrue(
            any(
                "select a file" in str(message).lower()
                for message in messages
            )
        )

    @patch(
        "apps.cleaner.views.DatasetIngestionService.ingest"
    )
    def test_upload_stores_only_ids_in_session(
        self,
        mock_ingest,
    ):
        dataset = self._create_dataset()

        job = self._create_job(
            dataset,
        )

        dataframe = pd.DataFrame(
            {
                "name": ["Amani"],
                "age": [20],
            }
        )

        class ImportResult:
            pass

        import_result = ImportResult()
        import_result.dataframe = dataframe

        class IngestionResult:
            pass

        ingestion = IngestionResult()
        ingestion.dataset = dataset
        ingestion.cleaning_job = job
        ingestion.import_result = import_result

        mock_ingest.return_value = ingestion

        uploaded_file = SimpleUploadedFile(
            "customers.csv",
            b"name,age\nAmani,20\n",
            content_type="text/csv",
        )

        response = self.client.post(
            reverse("cleaner:upload"),
            {"file": uploaded_file},
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        session = self.client.session

        self.assertEqual(
            session["dataset_id"],
            dataset.pk,
        )

        self.assertEqual(
            session["cleaning_job_id"],
            job.pk,
        )

        self.assertNotIn(
            "uploaded_file_path",
            session,
        )

        self.assertNotIn(
            "original_filename",
            session,
        )

        self.assertNotIn(
            "detected_format",
            session,
        )

    def test_get_session_job_data_requires_dataset(self):
        data, error = _get_session_job_data(
            self.client.request().wsgi_request,
        )

        self.assertEqual(
            data,
            {},
        )

        self.assertEqual(
            error,
            "No uploaded dataset was found.",
        )

    def test_get_session_job_data_requires_job(self):
        request = self.client.request().wsgi_request

        session = request.session
        session["dataset_id"] = 123
        session.save()

        request.session = session

        data, error = _get_session_job_data(
            request,
        )

        self.assertEqual(
            data,
            {},
        )

        self.assertEqual(
            error,
            "No cleaning job was found.",
        )

    def test_clean_requires_post(self):
        response = self.client.get(
            reverse("cleaner:clean"),
        )

        self.assertEqual(
            response.status_code,
            405,
        )

    def test_clean_without_session_redirects(self):
        response = self.client.post(
            reverse("cleaner:clean"),
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.url,
            reverse("cleaner:upload"),
        )

    def test_clean_with_missing_job_returns_404(self):
        dataset = self._create_dataset()

        session = self.client.session

        session["dataset_id"] = dataset.pk
        session["cleaning_job_id"] = 999999

        session.save()

        response = self.client.post(
            reverse("cleaner:clean"),
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_download_csv_without_session_redirects(self):
        response = self.client.get(
            reverse("cleaner:download_csv"),
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.url,
            reverse("cleaner:upload"),
        )

    def test_download_pdf_without_session_redirects(self):
        response = self.client.get(
            reverse("cleaner:download_pdf"),
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.url,
            reverse("cleaner:upload"),
        )

    def test_download_csv_uses_database_file(self):
        dataset = self._create_dataset()

        job = self._create_job(
            dataset,
        )

        output = CleaningJobOutput.objects.create(
            job=job,
            file_format=CleaningJobOutput.Format.CSV,
            filename="customers_cleaned.csv",
            content_type="text/csv",
        )

        output.file.save(
            "customers_cleaned.csv",
            ContentFile(
                b"name,age\nAmani,20\n",
            ),
        )

        self._set_workflow_session(
            dataset,
            job,
        )

        response = self.client.get(
            reverse("cleaner:download_csv"),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response["Content-Type"],
            "text/csv",
        )

        self.assertTrue(
            response["Content-Disposition"].endswith(
                ".csv\"",
            ),
        )


    def test_download_excel_uses_database_file(self):
        dataset = self._create_dataset()

        job = self._create_job(
            dataset,
        )

        output = CleaningJobOutput.objects.create(
            job=job,
            file_format=CleaningJobOutput.Format.XLSX,
            filename="customers_cleaned.xlsx",
            content_type=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
        )

        output.file.save(
            "customers_cleaned.xlsx",
            ContentFile(
                b"fake-xlsx-content",
            ),
        )

        self._set_workflow_session(
            dataset,
            job,
        )

        response = self.client.get(
            reverse("cleaner:download_excel"),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response["Content-Type"],
            (
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
        )

        self.assertTrue(
            response["Content-Disposition"].endswith(
                ".xlsx\"",
            ),
        )


    def test_download_pdf_uses_database_file(self):
        dataset = self._create_dataset()

        job = self._create_job(
            dataset,
        )

        output = CleaningJobOutput.objects.create(
            job=job,
            file_format=CleaningJobOutput.Format.PDF,
            filename="customers_cleaning_report.pdf",
            content_type="application/pdf",
        )

        output.file.save(
            "customers_cleaning_report.pdf",
            ContentFile(
                b"%PDF-test",
            ),
        )

        self._set_workflow_session(
            dataset,
            job,
        )

        response = self.client.get(
            reverse("cleaner:download_pdf"),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response["Content-Type"],
            "application/pdf",
        )

        self.assertTrue(
            response["Content-Disposition"].endswith(
                ".pdf\"",
            ),
        )


    def test_download_csv_rejects_pdf_file(self):
        dataset = self._create_dataset()

        job = self._create_job(
            dataset,
        )

        output = CleaningJobOutput.objects.create(
            job=job,
            file_format=CleaningJobOutput.Format.CSV,
            filename="wrong.pdf",
            content_type="application/pdf",
        )

        output.file.save(
            "wrong.pdf",
            ContentFile(
                b"%PDF-test",
            ),
        )

        self._set_workflow_session(
            dataset,
            job,
        )

        response = self.client.get(
            reverse("cleaner:download_csv"),
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.url,
            reverse("cleaner:upload"),
        )


    def test_download_excel_rejects_wrong_extension(self):
        dataset = self._create_dataset()

        job = self._create_job(
            dataset,
        )

        output = CleaningJobOutput.objects.create(
            job=job,
            file_format=CleaningJobOutput.Format.XLSX,
            filename="wrong.csv",
            content_type="text/csv",
        )

        output.file.save(
            "wrong.csv",
            ContentFile(
                b"name\nAmani\n",
            ),
        )

        self._set_workflow_session(
            dataset,
            job,
        )

        response = self.client.get(
            reverse("cleaner:download_excel"),
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.url,
            reverse("cleaner:upload"),
        )


    def test_download_excel_without_session_redirects(self):
        response = self.client.get(
            reverse("cleaner:download_excel"),
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.url,
            reverse("cleaner:upload"),
        )

    def test_download_pdf_rejects_csv_file(self):
        dataset = self._create_dataset()

        job = self._create_job(
            dataset,
        )

        output = CleaningJobOutput.objects.create(
            job=job,
            file_format=CleaningJobOutput.Format.PDF,
            filename="wrong.csv",
            content_type="text/csv",
        )

        output.file.save(
            "wrong.csv",
            ContentFile(
                b"name\nAmani\n",
            ),
        )

        self._set_workflow_session(
            dataset,
            job,
        )

        response = self.client.get(
            reverse("cleaner:download_pdf"),
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.url,
            reverse("cleaner:upload"),
        )


    def test_download_csv_missing_file_redirects(self):
        dataset = self._create_dataset()

        job = self._create_job(
            dataset,
        )

        self._set_workflow_session(
            dataset,
            job,
        )

        response = self.client.get(
            reverse("cleaner:download_csv"),
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.url,
            reverse("cleaner:upload"),
        )

    def test_clean_rejects_dataset_job_mismatch(self):
        dataset_one = self._create_dataset(
            "one.csv",
        )

        dataset_two = self._create_dataset(
            "two.csv",
        )

        job = self._create_job(
            dataset_two,
        )

        session = self.client.session

        session["dataset_id"] = dataset_one.pk
        session["cleaning_job_id"] = job.pk

        session.save()

        response = self.client.post(
            reverse("cleaner:clean"),
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.url,
            reverse("cleaner:upload"),
        )

    def test_scan_dataframe_returns_expected_statistics(self):
        dataframe = pd.DataFrame(
            {
                "name": [
                    "Amani",
                    "Amani",
                    None,
                ],
                "age": [
                    20,
                    20,
                    None,
                ],
            }
        )

        result = _scan_dataframe(
            dataframe,
        )

        self.assertEqual(
            result["rows"],
            3,
        )

        self.assertEqual(
            result["columns"],
            2,
        )

        self.assertEqual(
            result["missing_values"],
            2,
        )

        self.assertEqual(
            result["duplicate_rows"],
            1,
        )

