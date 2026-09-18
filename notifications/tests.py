from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from subscriptions.models import Subscription

from .models import Notification


class NotificationRelationshipTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username="notification-owner")
        cls.subscription = Subscription.objects.create(
            sub_name="Example",
            sub_price=100,
            sub_cycle_value=1,
            sub_cycle_unit="month",
            sub_start=date(2026, 1, 1),
            sub_next=date(2026, 2, 1),
            user=cls.user,
        )
        cls.notification = Notification.objects.create(
            notif_type="payment_reminder",
            notif_title="Payment due",
            notif_text="Your subscription payment is due.",
            notif_date=timezone.now(),
            notif_channel="WEB",
            sub=cls.subscription,
        )

    def test_notification_owner_is_reached_through_subscription(self):
        self.assertEqual(self.notification.sub.user, self.user)

    def test_notifications_can_be_filtered_by_subscription_owner(self):
        notifications = Notification.objects.filter(sub__user=self.user)

        self.assertQuerySetEqual(notifications, [self.notification])


class TopbarNotificationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model()
        cls.user = users.objects.create_user(username="bell-owner")
        cls.other_user = users.objects.create_user(username="other-bell-owner")
        cls.subscription = Subscription.objects.create(
            sub_name="Owner service",
            sub_start=date(2026, 1, 1),
            trial_status=True,
            trial_end=date(2026, 1, 8),
            user=cls.user,
        )
        cls.other_subscription = Subscription.objects.create(
            sub_name="Other service",
            sub_start=date(2026, 1, 1),
            trial_status=True,
            trial_end=date(2026, 1, 8),
            user=cls.other_user,
        )
        cls.notification = Notification.objects.create(
            notif_type="TRIAL_END",
            notif_title="Trial ใกล้สิ้นสุด",
            notif_text="บริการของคุณใกล้หมดช่วงทดลองใช้ฟรี",
            notif_date=timezone.now(),
            notif_channel="WEB",
            sub=cls.subscription,
        )
        cls.other_notification = Notification.objects.create(
            notif_type="TRIAL_END",
            notif_title="การแจ้งเตือนของคนอื่น",
            notif_text="ต้องไม่แสดง",
            notif_date=timezone.now(),
            notif_channel="WEB",
            sub=cls.other_subscription,
        )

    def setUp(self):
        self.client.force_login(self.user)

    def test_topbar_bell_only_shows_current_users_notifications(self):
        response = self.client.get(reverse("dashboard:index"))

        self.assertContains(response, 'id="notification-toggle"')
        self.assertContains(response, "Trial ใกล้สิ้นสุด")
        self.assertNotContains(response, "การแจ้งเตือนของคนอื่น")
        self.assertEqual(response.context["topbar_unread_count"], 1)

    def test_mark_all_read_only_updates_current_users_notifications(self):
        response = self.client.post(
            reverse("notifications:mark_all_read"),
            {"next": reverse("accounts:profile")},
        )

        self.assertRedirects(response, reverse("accounts:profile"))
        self.notification.refresh_from_db()
        self.other_notification.refresh_from_db()
        self.assertTrue(self.notification.notif_read)
        self.assertFalse(self.other_notification.notif_read)

# Create your tests here.
