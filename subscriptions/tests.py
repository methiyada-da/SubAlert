from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import Subscription


class SubscriptionValidationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username="subscriber")

    def subscription_data(self, **overrides):
        data = {
            "sub_name": "Example",
            "sub_price": 100,
            "sub_cycle_value": 1,
            "sub_cycle_unit": "month",
            "sub_start": date(2026, 1, 1),
            "sub_next": date(2026, 2, 1),
            "user": self.user,
        }
        data.update(overrides)
        return data

    def test_cycle_value_zero_fails_validation(self):
        subscription = Subscription(**self.subscription_data(sub_cycle_value=0))

        with self.assertRaises(ValidationError):
            subscription.full_clean()

    def test_negative_price_fails_validation(self):
        subscription = Subscription(**self.subscription_data(sub_price=-1))

        with self.assertRaises(ValidationError):
            subscription.full_clean()

    def test_database_rejects_zero_cycle_value(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Subscription.objects.create(**self.subscription_data(sub_cycle_value=0))

    def test_database_rejects_negative_price(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Subscription.objects.create(**self.subscription_data(sub_price=-1))

# Create your tests here.
