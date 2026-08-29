from __future__ import annotations

from django.test import TestCase

from apps.cleaner.models import CleaningFinding, CleaningJob


class CleaningJobModelTests(TestCase):

    def test_job_can_exist_without_original_file(self):
        job = CleaningJob.objects.create()

        self.assertFalse(
            job.original_file
        )

        self.assertEqual(
            job.status,
            CleaningJob.Status.PENDING,
        )

    def test_job_status_defaults_to_pending(self):
        job = CleaningJob.objects.create()

        self.assertEqual(
            job.status,
            CleaningJob.Status.PENDING,
        )

    def test_issue_counters_default_to_zero(self):
        job = CleaningJob.objects.create()

        self.assertEqual(
            job.row_count,
            0,
        )

        self.assertEqual(
            job.issues_found,
            0,
        )

        self.assertEqual(
            job.issues_fixed,
            0,
        )

        self.assertEqual(
            job.rows_removed,
            0,
        )

    def test_finding_belongs_to_job(self):
        job = CleaningJob.objects.create()

        finding = CleaningFinding.objects.create(
            job=job,
            finding_type=(
                CleaningFinding.FindingType.MISSING
            ),
            description="Missing values detected.",
        )

        self.assertEqual(
            finding.job,
            job,
        )

        self.assertEqual(
            job.findings.count(),
            1,
        )

    def test_deleting_job_deletes_findings(self):
        job = CleaningJob.objects.create()

        CleaningFinding.objects.create(
            job=job,
            finding_type=(
                CleaningFinding.FindingType.DUPLICATE
            ),
            description="Duplicate row detected.",
        )

        job.delete()

        self.assertEqual(
            CleaningFinding.objects.count(),
            0,
        )
