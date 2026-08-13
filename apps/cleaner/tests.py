from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import CleaningJob


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
            302,
        )

        self.assertEqual(
            CleaningJob.objects.count(),
            1,
        )

        job = CleaningJob.objects.first()

        self.assertEqual(
            job.filename,
            "customers.csv",
        )