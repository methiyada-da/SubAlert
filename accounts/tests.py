from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse


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


class AuthenticationFlowTests(TestCase):
    password = "Strong-Pass-2026!"

    def setUp(self):
        self.user_model = get_user_model()

    def test_register_page_is_available_to_anonymous_user(self):
        response = self.client.get(reverse("accounts:register"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/register.html")

    def test_registration_help_text_is_in_thai(self):
        response = self.client.get(reverse("accounts:register"))

        self.assertContains(response, "จำเป็นต้องกรอก ไม่เกิน 150 ตัวอักษร")
        self.assertContains(response, "รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร")
        self.assertContains(response, "กรอกรหัสผ่านเดิมอีกครั้งเพื่อยืนยัน")
        self.assertNotContains(response, "Required. 150 characters or fewer")
        self.assertNotContains(response, "Your password must contain")
        self.assertNotContains(response, "Enter the same password as before")

    def test_user_can_register(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "new-user",
                "email": "NEW@example.com",
                "password1": self.password,
                "password2": self.password,
            },
        )

        self.assertRedirects(response, reverse("accounts:login"))
        user = self.user_model.objects.get(username="new-user")
        self.assertEqual(user.email, "new@example.com")
        self.assertTrue(user.check_password(self.password))

    def test_registration_rejects_duplicate_email_case_insensitively(self):
        self.user_model.objects.create_user(
            username="existing",
            email="person@example.com",
            password=self.password,
        )

        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "another-user",
                "email": "PERSON@example.com",
                "password1": self.password,
                "password2": self.password,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "อีเมลนี้ถูกใช้งานแล้ว")
        self.assertFalse(self.user_model.objects.filter(username="another-user").exists())

    def test_authenticated_user_is_redirected_away_from_register(self):
        user = self.user_model.objects.create_user(
            username="signed-in",
            password=self.password,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("accounts:register"))

        self.assertRedirects(response, reverse("dashboard:index"))

    def test_user_can_log_in_and_log_out(self):
        self.user_model.objects.create_user(
            username="member",
            password=self.password,
        )

        login_response = self.client.post(
            reverse("accounts:login"),
            {"username": "member", "password": self.password},
        )
        self.assertRedirects(login_response, reverse("dashboard:index"))

        logout_response = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(logout_response, reverse("accounts:login"))

        dashboard_response = self.client.get(reverse("dashboard:index"))
        expected_login_url = (
            f"{reverse('accounts:login')}?next={reverse('dashboard:index')}"
        )
        self.assertRedirects(dashboard_response, expected_login_url)
