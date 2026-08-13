from django.test import TestCase
from django.urls import reverse


class DashboardTests(TestCase):

    def test_dashboard_loads(self):

        response = self.client.get(
            reverse("dashboard:index")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "dashboard/index.html",
        )