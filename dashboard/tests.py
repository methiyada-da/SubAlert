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
            sub_category="ซอฟต์แวร์",
            sub_platform="เว็บไซต์",
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

    def test_dashboard_separates_trial_end_from_payment_due(self):
        trial = Subscription.objects.create(
            sub_name="Seven day trial",
            sub_category="การศึกษา",
            sub_start=date(2026, 1, 1),
            trial_status=True,
            trial_end=date(2026, 1, 8),
            user=self.user,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("dashboard:index"))

        self.assertIn(trial, response.context["active_trials"])
        self.assertNotIn(trial, response.context["upcoming_subscriptions"])
        self.assertContains(response, "ทดลองใช้ฟรี")
        self.assertContains(response, "Seven day trial")

    def test_dashboard_has_persistent_shell_and_overview_content(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("dashboard:index"))

        self.assertContains(response, 'id="app-sidebar"')
        self.assertContains(response, 'id="global-service-search"')
        self.assertContains(response, 'id="notification-toggle"')
        self.assertContains(response, reverse("accounts:profile"))
        self.assertContains(response, "ภาพรวมการติดตาม")
        self.assertContains(response, "รอบชำระถัดไป")
        self.assertContains(response, "เพิ่มบริการใหม่")
        self.assertContains(response, "js/app_shell.js")
        self.assertNotContains(response, 'id="service-filters"')

    def test_line_banner_is_optional_and_hidden_when_ready(self):
        self.client.force_login(self.user)
        disconnected = self.client.get(reverse("dashboard:index"))
        self.assertContains(disconnected, "รับการแจ้งเตือนผ่าน LINE")
        self.assertContains(disconnected, reverse("line_connect"))

        self.user.line_id = "UREADY"
        self.user.line_status = 2
        self.user.save(update_fields=["line_id", "line_status"])
        ready = self.client.get(reverse("dashboard:index"))
        self.assertNotContains(ready, "รับการแจ้งเตือนผ่าน LINE")
