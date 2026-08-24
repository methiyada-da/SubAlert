from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from subscriptions.models import Subscription


class DashboardAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()
        cls.user = user_model.objects.create_user(
            username="dashboard-user",
            password="Strong-Pass-2026!",
        )
        cls.other_user = user_model.objects.create_user(
            username="other-user",
            password="Strong-Pass-2026!",
        )
        Subscription.objects.create(
            sub_name="Active subscription",
            sub_price=100,
            sub_cycle_value=1,
            sub_cycle_unit="month",
            sub_start=date(2026, 1, 1),
            sub_next=date(2026, 2, 1),
            user=cls.user,
        )
        Subscription.objects.create(
            sub_name="Inactive subscription",
            sub_price=50,
            sub_cycle_value=1,
            sub_cycle_unit="month",
            sub_start=date(2026, 1, 1),
            sub_next=date(2026, 3, 1),
            sub_status=False,
            user=cls.user,
        )
        Subscription.objects.create(
            sub_name="Other user's subscription",
            sub_price=200,
            sub_cycle_value=1,
            sub_cycle_unit="month",
            sub_start=date(2026, 1, 1),
            sub_next=date(2026, 2, 1),
            user=cls.other_user,
        )

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(reverse("dashboard:index"))
        expected_login_url = (
            f"{reverse('accounts:login')}?next={reverse('dashboard:index')}"
        )

        self.assertRedirects(response, expected_login_url)

    def test_dashboard_only_counts_current_users_subscriptions(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("dashboard:index"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/dashboard.html")
        self.assertEqual(response.context["subscription_count"], 2)
        self.assertEqual(response.context["active_subscription_count"], 1)
        self.assertContains(response, "Active subscription")
        self.assertNotContains(response, "Other user&#x27;s subscription")
