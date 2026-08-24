from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase


class UserLineIdTests(TestCase):
    def test_blank_line_id_is_stored_as_null(self):
        user = get_user_model().objects.create_user(
            username="without-line",
            line_id="",
        )

        user.refresh_from_db()

        self.assertIsNone(user.line_id)

    def test_line_id_must_be_unique(self):
        user_model = get_user_model()
        user_model.objects.create_user(username="first", line_id="U123")

        with self.assertRaises(IntegrityError), transaction.atomic():
            user_model.objects.create_user(username="second", line_id="U123")
