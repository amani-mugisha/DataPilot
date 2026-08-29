from __future__ import annotations

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.cleaner.models import (
    CleaningFinding,
    CleaningJob,
)
from apps.datasets.models import Dataset


class ReportViewTests(TestCase):

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
        *,
        status: str = CleaningJob.Status.COMPLETED,
    ) -> CleaningJob:
        return CleaningJob.objects.create(
            dataset=dataset,
            original_file=(
                dataset.original_file
                if dataset
                else None
            ),
            status=status,
            row_count=100,
            issues_found=10,
            issues_fixed=8,
            rows_removed=2,
        )

    def test_history_renders_successfully(self):
        response = self.client.get(
            reverse("reports:history"),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "reports/history.html",
        )

    def test_history_contains_completed_job(self):
        dataset = self._create_dataset()
        job = self._create_job(dataset)

        response = self.client.get(
            reverse("reports:history"),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            dataset.name,
        )

        self.assertContains(
            response,
            f"View",
        )

        self.assertContains(
            response,
            str(job.row_count),
        )

    def test_history_shows_empty_state_without_jobs(self):
        response = self.client.get(
            reverse("reports:history"),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "No cleaning history yet",
        )

        self.assertContains(
            response,
            "Clean your first file",
        )

    def test_history_paginates_jobs(self):
        dataset = self._create_dataset()

        for _ in range(25):
            self._create_job(dataset)

        response = self.client.get(
            reverse("reports:history"),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        jobs = response.context["jobs"]

        self.assertEqual(
            jobs.number,
            1,
        )

        self.assertEqual(
            jobs.paginator.num_pages,
            2,
        )

        self.assertTrue(
            jobs.has_next(),
        )

    def test_history_second_page_works(self):
        dataset = self._create_dataset()

        for _ in range(25):
            self._create_job(dataset)

        response = self.client.get(
            reverse("reports:history") + "?page=2",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        jobs = response.context["jobs"]

        self.assertEqual(
            jobs.number,
            2,
        )

        self.assertFalse(
            jobs.has_next(),
        )

    def test_report_renders_successfully(self):
        dataset = self._create_dataset()
        job = self._create_job(dataset)

        response = self.client.get(
            reverse(
                "reports:report",
                args=[job.pk],
            ),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "reports/report.html",
        )

    def test_report_contains_job_information(self):
        dataset = self._create_dataset()
        job = self._create_job(dataset)

        response = self.client.get(
            reverse(
                "reports:report",
                args=[job.pk],
            ),
        )

        self.assertContains(
            response,
            dataset.name,
        )

        self.assertContains(
            response,
            f"Job #{job.pk}",
        )

        self.assertContains(
            response,
            "Cleaning details",
        )

    def test_report_contains_summary_statistics(self):
        dataset = self._create_dataset()
        job = self._create_job(dataset)

        response = self.client.get(
            reverse(
                "reports:report",
                args=[job.pk],
            ),
        )

        self.assertContains(
            response,
            "Rows processed",
        )

        self.assertContains(
            response,
            str(job.row_count),
        )

        self.assertContains(
            response,
            str(job.issues_found),
        )

        self.assertContains(
            response,
            str(job.issues_fixed),
        )

        self.assertContains(
            response,
            str(job.rows_removed),
        )

    def test_report_contains_findings(self):
        dataset = self._create_dataset()
        job = self._create_job(dataset)

        CleaningFinding.objects.create(
            job=job,
            finding_type=(
                CleaningFinding.FindingType.DUPLICATE
            ),
            column_name="email",
            row_number=12,
            description="Duplicate email address.",
            fixed=True,
        )

        response = self.client.get(
            reverse(
                "reports:report",
                args=[job.pk],
            ),
        )

        self.assertContains(
            response,
            "Duplicate Row",
        )

        self.assertContains(
            response,
            "email",
        )

        self.assertContains(
            response,
            "Duplicate email address.",
        )

        self.assertContains(
            response,
            "Fixed",
        )

    def test_report_returns_404_for_unknown_job(self):
        response = self.client.get(
            reverse(
                "reports:report",
                args=[999999],
            ),
        )

        self.assertEqual(
            response.status_code,
            404,
        )
