from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import CleaningJob
from apps.datasets.models import Dataset


class CleanerUploadTests(TestCase):

    def test_upload_page(self):
        response = self.client.get(
            reverse("cleaner:upload")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_csv_upload(self):
        csv_file = SimpleUploadedFile(
            "customers.csv",
            b"id,name\n1,Amani\n2,John\n",
            content_type="text/csv",
        )

        response = self.client.post(
            reverse("cleaner:upload"),
            {
                "file": csv_file,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            Dataset.objects.count(),
            1,
        )

        self.assertEqual(
            CleaningJob.objects.count(),
            1,
        )

        job = CleaningJob.objects.select_related("dataset").first()

        self.assertIsNotNone(job)

        self.assertEqual(
            job.dataset.name,
            "customers.csv",
        )

        self.assertEqual(
            job.row_count,
            2,
        )

        self.assertEqual(
            job.dataset.row_count,
            2,
        )

        self.assertEqual(
            job.dataset.column_count,
            2,
        )

        self.assertEqual(
            job.status,
            CleaningJob.Status.PENDING,
        )
