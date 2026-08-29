from __future__ import annotations

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.cleaner.models import (
    CleaningFinding,
    CleaningJob,
    CleaningJobOutput,
)
from apps.datasets.models import Dataset
from apps.reports.services import (
    get_job_history,
    get_job_report,
)


class ReportServiceTests(TestCase):

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
        row_count: int = 2,
        issues_found: int = 3,
        issues_fixed: int = 2,
        rows_removed: int = 1,
    ) -> CleaningJob:
        return CleaningJob.objects.create(
            dataset=dataset,
            original_file=(
                dataset.original_file
                if dataset
                else None
            ),
            status=status,
            row_count=row_count,
            issues_found=issues_found,
            issues_fixed=issues_fixed,
            rows_removed=rows_removed,
        )

    def test_get_job_history_returns_newest_first(self):
        dataset = self._create_dataset()

        older = self._create_job(dataset)
        newer = self._create_job(dataset)

        jobs = list(get_job_history())

        self.assertEqual(
            [job.pk for job in jobs],
            [newer.pk, older.pk],
        )

    def test_get_job_history_includes_dataset(self):
        dataset = self._create_dataset(
            "customers.csv",
        )

        job = self._create_job(dataset)

        result = get_job_history()

        history_job = result.get(
            pk=job.pk,
        )

        self.assertEqual(
            history_job.dataset,
            dataset,
        )

    def test_get_job_history_respects_limit(self):
        dataset = self._create_dataset()

        self._create_job(dataset)
        self._create_job(dataset)
        newest = self._create_job(dataset)

        jobs = list(
            get_job_history(limit=2)
        )

        self.assertEqual(
            len(jobs),
            2,
        )

        self.assertEqual(
            jobs[0].pk,
            newest.pk,
        )

    def test_get_job_history_returns_empty_queryset_when_no_jobs(self):
        jobs = get_job_history()

        self.assertEqual(
            jobs.count(),
            0,
        )

    def test_get_job_report_returns_job(self):
        dataset = self._create_dataset()
        job = self._create_job(dataset)

        context = get_job_report(job)

        self.assertIs(
            context["job"],
            job,
        )

    def test_get_job_report_returns_findings(self):
        dataset = self._create_dataset()
        job = self._create_job(dataset)

        finding = CleaningFinding.objects.create(
            job=job,
            finding_type=(
                CleaningFinding.FindingType.MISSING
            ),
            column_name="email",
            row_number=4,
            description="Missing email address.",
            fixed=True,
        )

        context = get_job_report(job)

        self.assertEqual(
            list(context["findings"]),
            [finding],
        )

    def test_get_job_report_builds_summary(self):
        dataset = self._create_dataset()
        job = self._create_job(
            dataset,
            row_count=100,
            issues_found=15,
            issues_fixed=12,
            rows_removed=3,
        )

        context = get_job_report(job)

        self.assertEqual(
            context["summary"],
            {
                "row_count": 100,
                "issues_found": 15,
                "issues_fixed": 12,
                "rows_removed": 3,
            },
        )

    def test_get_job_report_returns_cleaned_file_url(self):
        dataset = self._create_dataset()
        job = self._create_job(dataset)

        output = CleaningJobOutput.objects.create(
            job=job,
            file=SimpleUploadedFile(
                "customers_cleaned.csv",
                b"name,age\nAmani,20\n",
                content_type="text/csv",
            ),
            file_format=CleaningJobOutput.Format.CSV,
            filename="customers_cleaned.csv",
            content_type="text/csv",
        )

        context = get_job_report(job)

        self.assertEqual(
            context["download_url"],
            output.file.url,
        )

    def test_get_job_report_has_no_download_url_without_legacy_file(
        self,
    ):
        dataset = self._create_dataset()
        job = self._create_job(dataset)

        context = get_job_report(job)

        self.assertIsNone(
            context["download_url"],
        )
