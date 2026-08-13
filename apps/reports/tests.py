from django.test import TestCase
from django.urls import reverse


class ReportsTests(TestCase):

    def test_history_page_loads(self):

        response = self.client.get(
            reverse("reports:history")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "reports/history.html",
        )