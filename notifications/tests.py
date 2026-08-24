from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
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

# Create your tests here.
