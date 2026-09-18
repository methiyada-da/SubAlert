import base64
import hashlib
import hmac
import json
from datetime import date
from io import StringIO
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError, transaction
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from notifications.models import Notification
from subscriptions.models import Subscription

from .line_login import LineAPIError, send_line_push_message


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

    def test_registration_password_errors_are_in_thai(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "thai-errors-user",
                "email": "thai-errors@example.com",
                "password1": "123",
                "password2": "123",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "รหัสผ่านสั้นเกินไป ต้องมีอย่างน้อย 8 ตัวอักษร")
        self.assertContains(response, "รหัสผ่านนี้เป็นรหัสผ่านที่ใช้กันทั่วไป")
        self.assertContains(response, "รหัสผ่านต้องไม่เป็นตัวเลขทั้งหมด")
        self.assertNotContains(response, "This password is too short")
        self.assertNotContains(response, "This password is too common")
        self.assertNotContains(response, "This password is entirely numeric")

    def test_registration_password_mismatch_error_is_in_thai(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "mismatch-user",
                "email": "mismatch@example.com",
                "password1": self.password,
                "password2": "Different-Strong-Pass-2026!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "รหัสผ่านทั้งสองช่องไม่ตรงกัน")
        self.assertNotContains(response, "The two password fields didn’t match")

    def test_success_message_has_auto_dismiss_controls(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "message-user",
                "email": "message@example.com",
                "password1": self.password,
                "password2": self.password,
            },
            follow=True,
        )

        self.assertContains(response, "สมัครสมาชิกสำเร็จ กรุณาเข้าสู่ระบบ")
        self.assertContains(response, "data-auto-dismiss")
        self.assertContains(response, 'class="message-close"')
        self.assertContains(response, "js/messages.js")

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


class ProfileManagementTests(TestCase):
    password = "Strong-Pass-2026!"

    def setUp(self):
        users = get_user_model()
        self.user = users.objects.create_user(
            username="profile-user",
            email="profile@example.com",
            password=self.password,
        )
        self.other_user = users.objects.create_user(
            username="other-profile",
            email="other@example.com",
            password=self.password,
        )

    def test_profile_requires_login(self):
        response = self.client.get(reverse("accounts:profile"))
        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('accounts:profile')}",
        )

    def test_profile_page_shows_member_details_and_app_shell(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("accounts:profile"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "โปรไฟล์ของฉัน")
        self.assertContains(response, "รายละเอียดสมาชิก")
        self.assertContains(response, "การเชื่อมต่อ LINE")
        self.assertContains(response, "เชื่อมต่อ LINE")
        self.assertContains(response, "เปลี่ยนรหัสผ่าน")
        self.assertContains(response, 'id="app-sidebar"')

    def test_user_can_update_own_profile(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("accounts:profile"),
            {
                "username": "updated-profile",
                "email": "UPDATED@example.com",
            },
        )

        self.assertRedirects(response, reverse("accounts:profile"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "updated-profile")
        self.assertEqual(self.user.email, "updated@example.com")

    def test_profile_rejects_another_users_email(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("accounts:profile"),
            {
                "username": self.user.username,
                "email": "OTHER@example.com",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "อีเมลนี้ถูกใช้งานแล้ว")

    def test_user_can_change_password_without_being_logged_out(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("accounts:password_change"),
            {
                "old_password": self.password,
                "new_password1": "New-Strong-Pass-2026!",
                "new_password2": "New-Strong-Pass-2026!",
            },
        )

        self.assertRedirects(response, reverse("accounts:profile"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("New-Strong-Pass-2026!"))
        self.assertEqual(self.client.get(reverse("accounts:profile")).status_code, 200)


@override_settings(
    LINE_LOGIN_CHANNEL_ID="1234567890",
    LINE_LOGIN_CHANNEL_SECRET="test-channel-secret",
    LINE_CALLBACK_URL="https://example.com/line/callback/",
    LINE_HTTP_TIMEOUT=3,
)
class LineLoginTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="line-user")
        self.client.force_login(self.user)

    def set_oauth_state(self, state="valid-state"):
        session = self.client.session
        session["line_oauth_state"] = state
        session.save()

    def test_line_urls_match_required_routes(self):
        self.assertEqual(reverse("line_connect"), "/line/connect/")
        self.assertEqual(reverse("line_callback"), "/line/callback/")

    def test_connect_requires_authenticated_subalert_user(self):
        self.client.logout()
        response = self.client.get(reverse("line_connect"))
        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('line_connect')}",
        )

    def test_connect_creates_state_and_redirects_with_encoded_parameters(self):
        response = self.client.get(reverse("line_connect"))

        self.assertEqual(response.status_code, 302)
        parsed = urlparse(response.url)
        query = parse_qs(parsed.query)
        self.assertEqual(
            f"{parsed.scheme}://{parsed.netloc}{parsed.path}",
            "https://access.line.me/oauth2/v2.1/authorize",
        )
        self.assertEqual(query["response_type"], ["code"])
        self.assertEqual(query["client_id"], ["1234567890"])
        self.assertEqual(query["redirect_uri"], ["https://example.com/line/callback/"])
        self.assertEqual(query["scope"], ["openid profile"])
        self.assertEqual(query["bot_prompt"], ["aggressive"])
        self.assertEqual(query["state"], [self.client.session["line_oauth_state"]])
        self.assertNotIn("test-channel-secret", response.url)

    @override_settings(LINE_LOGIN_CHANNEL_SECRET="")
    def test_connect_handles_missing_environment_configuration(self):
        response = self.client.get(reverse("line_connect"), follow=True)
        self.assertRedirects(response, reverse("accounts:profile"))
        self.assertContains(response, "ระบบตั้งค่า LINE Login ไม่ครบ")

    @patch("accounts.views.exchange_code_for_token")
    def test_callback_rejects_invalid_state_before_calling_line(self, exchange):
        self.set_oauth_state("expected")
        response = self.client.get(
            reverse("line_callback"),
            {"code": "auth-code", "state": "wrong"},
            follow=True,
        )

        exchange.assert_not_called()
        self.user.refresh_from_db()
        self.assertIsNone(self.user.line_id)
        self.assertEqual(self.user.line_status, 0)
        self.assertContains(response, "ข้อมูลยืนยันไม่ถูกต้อง")
        self.assertNotIn("line_oauth_state", self.client.session)


@override_settings(
    LINE_MESSAGING_CHANNEL_SECRET="test-messaging-channel-secret",
    LINE_MESSAGING_CHANNEL_ACCESS_TOKEN="test-access-token",
)
class LineWebhookTests(TestCase):
    channel_secret = "test-messaging-channel-secret"

    def setUp(self):
        self.user_model = get_user_model()
        self.user = self.user_model.objects.create_user(
            username="webhook-user",
            line_id="UWEBHOOKUSER",
            line_status=1,
        )

    def signed_post(self, payload, *, signature_secret=None):
        raw_body = json.dumps(
            payload,
            separators=(",", ":"),
        ).encode("utf-8")
        secret = signature_secret or self.channel_secret
        signature = base64.b64encode(
            hmac.new(
                secret.encode("utf-8"),
                raw_body,
                hashlib.sha256,
            ).digest()
        ).decode("ascii")
        return self.client.post(
            reverse("line_webhook"),
            data=raw_body,
            content_type="application/json",
            HTTP_X_LINE_SIGNATURE=signature,
        )

    def test_webhook_url_matches_required_route_and_accepts_only_post(self):
        self.assertEqual(reverse("line_webhook"), "/line/webhook/")
        self.assertEqual(self.client.get(reverse("line_webhook")).status_code, 405)

    def test_valid_signature_returns_200(self):
        response = self.signed_post({"events": [{"type": "message"}]})

        self.assertEqual(response.status_code, 200)

    def test_invalid_signature_is_rejected_without_processing_event(self):
        response = self.signed_post(
            {
                "events": [
                    {
                        "type": "follow",
                        "source": {"type": "user", "userId": self.user.line_id},
                    }
                ]
            },
            signature_secret="wrong-channel-secret",
        )

        self.assertEqual(response.status_code, 400)
        self.user.refresh_from_db()
        self.assertEqual(self.user.line_status, 1)

    def test_verify_webhook_request_with_empty_events_returns_200(self):
        response = self.signed_post(
            {"destination": "UDESTINATION", "events": []},
        )

        self.assertEqual(response.status_code, 200)

    def test_follow_event_changes_line_status_from_one_to_two(self):
        response = self.signed_post(
            {
                "events": [
                    {
                        "type": "follow",
                        "source": {"type": "user", "userId": self.user.line_id},
                    }
                ]
            }
        )

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.line_status, 2)

    def test_unfollow_event_changes_status_to_one_and_keeps_line_id(self):
        self.user.line_status = 2
        self.user.save(update_fields=["line_status"])

        response = self.signed_post(
            {
                "events": [
                    {
                        "type": "unfollow",
                        "source": {"type": "user", "userId": self.user.line_id},
                    }
                ]
            }
        )

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.line_status, 1)
        self.assertEqual(self.user.line_id, "UWEBHOOKUSER")

    def test_unknown_line_user_returns_200_without_creating_user(self):
        user_count = self.user_model.objects.count()

        response = self.signed_post(
            {
                "events": [
                    {
                        "type": "follow",
                        "source": {"type": "user", "userId": "UUNKNOWNUSER"},
                    }
                ]
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.user_model.objects.count(), user_count)

    def test_other_event_type_is_ignored_and_returns_200(self):
        response = self.signed_post(
            {
                "events": [
                    {
                        "type": "message",
                        "source": {"type": "user", "userId": self.user.line_id},
                    }
                ]
            }
        )

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.line_status, 1)

    def test_multiple_events_are_processed_in_one_request(self):
        other_user = self.user_model.objects.create_user(
            username="second-webhook-user",
            line_id="USECONDWEBHOOKUSER",
            line_status=2,
        )

        response = self.signed_post(
            {
                "events": [
                    {
                        "type": "follow",
                        "source": {"type": "user", "userId": self.user.line_id},
                    },
                    {
                        "type": "unfollow",
                        "source": {"type": "user", "userId": other_user.line_id},
                    },
                ]
            }
        )

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        other_user.refresh_from_db()
        self.assertEqual(self.user.line_status, 2)
        self.assertEqual(other_user.line_status, 1)


@override_settings(
    LINE_LOGIN_CHANNEL_ID="1234567890",
    LINE_LOGIN_CHANNEL_SECRET="test-channel-secret",
    LINE_CALLBACK_URL="https://example.com/line/callback/",
    LINE_HTTP_TIMEOUT=3,
)
class LineLoginCallbackTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="line-user")
        self.client.force_login(self.user)

    def set_oauth_state(self, state="valid-state"):
        session = self.client.session
        session["line_oauth_state"] = state
        session.save()

    @patch("accounts.views.exchange_code_for_token")
    def test_callback_handles_line_error_response_without_linking(self, exchange):
        self.set_oauth_state()
        response = self.client.get(
            reverse("line_callback"),
            {"error": "access_denied", "state": "valid-state"},
            follow=True,
        )

        exchange.assert_not_called()
        self.user.refresh_from_db()
        self.assertIsNone(self.user.line_id)
        self.assertContains(response, "ยกเลิกการเชื่อมต่อบัญชี LINE แล้ว")

    @patch("accounts.views.fetch_friendship_status", return_value=False)
    @patch("accounts.views.fetch_line_profile")
    @patch("accounts.views.exchange_code_for_token", return_value="access-token")
    def test_callback_saves_user_id_not_display_name_and_sets_status_one(
        self,
        exchange,
        profile,
        friendship,
    ):
        profile.return_value = {
            "userId": "U1234567890",
            "displayName": "This is not the LINE ID",
        }
        self.set_oauth_state()

        response = self.client.get(
            reverse("line_callback"),
            {"code": "auth-code", "state": "valid-state"},
        )

        self.assertRedirects(response, reverse("accounts:profile"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.line_id, "U1234567890")
        self.assertNotEqual(self.user.line_id, "This is not the LINE ID")
        self.assertEqual(self.user.line_status, 1)
        exchange.assert_called_once_with("auth-code")
        profile.assert_called_once_with("access-token")
        friendship.assert_called_once_with("access-token")

    @patch("accounts.views.fetch_friendship_status", return_value=True)
    @patch(
        "accounts.views.fetch_line_profile",
        return_value={"userId": "UFRIEND123"},
    )
    @patch("accounts.views.exchange_code_for_token", return_value="access-token")
    def test_callback_sets_status_two_when_friendship_is_verified(
        self,
        exchange,
        profile,
        friendship,
    ):
        self.set_oauth_state()
        self.client.get(
            reverse("line_callback"),
            {"code": "auth-code", "state": "valid-state"},
        )

        self.user.refresh_from_db()
        self.assertEqual(self.user.line_id, "UFRIEND123")
        self.assertEqual(self.user.line_status, 2)

    @patch("accounts.views.fetch_friendship_status", return_value=True)
    @patch(
        "accounts.views.fetch_line_profile",
        return_value={"userId": "UALREADYUSED"},
    )
    @patch("accounts.views.exchange_code_for_token", return_value="access-token")
    def test_callback_does_not_overwrite_duplicate_line_id(
        self,
        exchange,
        profile,
        friendship,
    ):
        get_user_model().objects.create_user(
            username="existing-line-owner",
            line_id="UALREADYUSED",
            line_status=2,
        )
        self.set_oauth_state()
        response = self.client.get(
            reverse("line_callback"),
            {"code": "auth-code", "state": "valid-state"},
            follow=True,
        )

        self.user.refresh_from_db()
        self.assertIsNone(self.user.line_id)
        self.assertEqual(self.user.line_status, 0)
        self.assertContains(response, "เชื่อมกับบัญชี SubAlert อื่นอยู่แล้ว")

    @patch(
        "accounts.views.exchange_code_for_token",
        side_effect=LineAPIError("network failure"),
    )
    def test_callback_handles_network_errors_without_server_error(self, exchange):
        self.set_oauth_state()
        response = self.client.get(
            reverse("line_callback"),
            {"code": "auth-code", "state": "valid-state"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "เชื่อมต่อกับ LINE ไม่สำเร็จ")
        self.user.refresh_from_db()
        self.assertIsNone(self.user.line_id)

    @patch("accounts.views.fetch_line_profile", return_value={"userId": " @official "})
    @patch("accounts.views.exchange_code_for_token", return_value="access-token")
    def test_callback_rejects_official_account_basic_id(self, exchange, profile):
        self.set_oauth_state()
        response = self.client.get(
            reverse("line_callback"),
            {"code": "auth-code", "state": "valid-state"},
            follow=True,
        )

        self.assertContains(response, "User ID ที่ถูกต้อง")
        self.user.refresh_from_db()
        self.assertIsNone(self.user.line_id)


@override_settings(
    LINE_MESSAGING_CHANNEL_ACCESS_TOKEN="test-messaging-access-token",
    LINE_HTTP_TIMEOUT=4,
)
class LineMessagingAPIClientTests(TestCase):
    @patch("accounts.line_login.urlopen")
    def test_push_message_sends_expected_request(self, urlopen):
        response = MagicMock()
        response.read.return_value = b"{}"
        urlopen.return_value.__enter__.return_value = response

        send_line_push_message("ULINETARGET", "ข้อความทดสอบ")

        request = urlopen.call_args.args[0]
        self.assertEqual(
            request.full_url,
            "https://api.line.me/v2/bot/message/push",
        )
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(
            request.get_header("Authorization"),
            "Bearer test-messaging-access-token",
        )
        self.assertEqual(request.get_header("Content-type"), "application/json")
        self.assertEqual(
            json.loads(request.data.decode("utf-8")),
            {
                "to": "ULINETARGET",
                "messages": [{"type": "text", "text": "ข้อความทดสอบ"}],
            },
        )
        self.assertEqual(urlopen.call_args.kwargs["timeout"], 4)

    @patch("accounts.line_login.urlopen")
    def test_line_api_error_is_converted_to_safe_error(self, urlopen):
        urlopen.side_effect = HTTPError(
            url="https://api.line.me/v2/bot/message/push",
            code=400,
            msg="Bad Request",
            hdrs=None,
            fp=None,
        )

        with self.assertRaises(LineAPIError):
            send_line_push_message("ULINETARGET", "ข้อความทดสอบ")

    @patch("accounts.line_login.urlopen")
    def test_network_error_is_converted_to_safe_error(self, urlopen):
        urlopen.side_effect = URLError("network unavailable")

        with self.assertRaises(LineAPIError):
            send_line_push_message("ULINETARGET", "ข้อความทดสอบ")


@override_settings(
    LINE_MESSAGING_CHANNEL_ACCESS_TOKEN="test-messaging-access-token",
)
class LineTestMessageViewTests(TestCase):
    expected_message = (
        "🔔 ทดสอบการแจ้งเตือนจาก SubAlert\n"
        "การเชื่อมต่อ LINE พร้อมใช้งานแล้ว"
    )

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="line-message-user",
            line_id="ULINEMESSAGEUSER",
            line_status=2,
        )
        self.client.force_login(self.user)

    @patch("accounts.views.send_line_push_message")
    def test_ready_user_can_send_test_message(self, send_message):
        response = self.client.post(
            reverse("line_test_message"),
            follow=True,
        )

        self.assertEqual(reverse("line_test_message"), "/line/test-message/")
        self.assertRedirects(response, reverse("accounts:profile"))
        send_message.assert_called_once_with(
            self.user.line_id,
            self.expected_message,
        )
        self.assertContains(response, "ส่งข้อความทดสอบเรียบร้อยแล้ว")

    @patch("accounts.views.send_line_push_message")
    def test_user_with_status_other_than_two_cannot_send(self, send_message):
        self.user.line_status = 1
        self.user.save(update_fields=["line_status"])

        response = self.client.post(
            reverse("line_test_message"),
            follow=True,
        )

        send_message.assert_not_called()
        self.assertContains(response, "LINE ยังไม่พร้อมรับการแจ้งเตือน")

    @patch("accounts.views.send_line_push_message")
    def test_user_without_line_id_cannot_send(self, send_message):
        self.user.line_id = None
        self.user.save(update_fields=["line_id"])

        response = self.client.post(
            reverse("line_test_message"),
            follow=True,
        )

        send_message.assert_not_called()
        self.assertContains(response, "LINE ยังไม่พร้อมรับการแจ้งเตือน")

    @patch(
        "accounts.views.send_line_push_message",
        side_effect=LineAPIError("LINE rejected the request"),
    )
    def test_line_api_failure_returns_to_profile_without_500(self, send_message):
        response = self.client.post(
            reverse("line_test_message"),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ส่งข้อความทดสอบไม่สำเร็จ")

    @patch("accounts.views.send_line_push_message")
    def test_endpoint_accepts_only_post(self, send_message):
        response = self.client.get(reverse("line_test_message"))

        self.assertEqual(response.status_code, 405)
        send_message.assert_not_called()

    @patch("accounts.views.send_line_push_message")
    def test_post_requires_csrf_token(self, send_message):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.user)

        response = csrf_client.post(reverse("line_test_message"))

        self.assertEqual(response.status_code, 403)
        send_message.assert_not_called()

    def test_profile_shows_test_button_only_when_line_is_ready(self):
        ready_response = self.client.get(reverse("accounts:profile"))
        self.assertContains(ready_response, "ส่งข้อความทดสอบ")

        self.user.line_status = 1
        self.user.save(update_fields=["line_status"])
        pending_response = self.client.get(reverse("accounts:profile"))
        self.assertNotContains(pending_response, "ส่งข้อความทดสอบ")


class ResetLineDemoCommandTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="demo-user",
            email="demo@example.com",
            password="Strong-Pass-2026!",
            line_id="UDEMOUSER",
            line_status=2,
        )
        self.subscription = Subscription.objects.create(
            sub_name="Demo trial",
            sub_start=date(2026, 8, 1),
            trial_status=True,
            trial_end=date(2026, 8, 8),
            user=self.user,
        )
        self.notification = Notification.objects.create(
            notif_type="TRIAL_END",
            notif_title="Demo reminder",
            notif_text="Trial is ending",
            notif_date=timezone.now(),
            notif_channel="LINE",
            sub=self.subscription,
        )

    def test_reset_line_connection_successfully(self):
        output = StringIO()

        call_command("reset_line_demo", self.user.username, stdout=output)

        self.user.refresh_from_db()
        self.assertIsNone(self.user.line_id)
        self.assertEqual(self.user.line_status, 0)
        self.assertIn(
            "Reset LINE connection for demo-user successfully.",
            output.getvalue(),
        )

    def test_missing_username_raises_clear_command_error(self):
        with self.assertRaisesMessage(
            CommandError,
            'User "missing-user" was not found.',
        ):
            call_command("reset_line_demo", "missing-user")

    def test_reset_does_not_change_other_user_or_related_data(self):
        original_user_data = {
            "pk": self.user.pk,
            "username": self.user.username,
            "email": self.user.email,
            "password": self.user.password,
            "is_active": self.user.is_active,
            "date_joined": self.user.date_joined,
        }
        subscription_id = self.subscription.pk
        notification_id = self.notification.pk

        call_command("reset_line_demo", self.user.username, stdout=StringIO())

        self.user.refresh_from_db()
        self.subscription.refresh_from_db()
        self.notification.refresh_from_db()
        for field_name, original_value in original_user_data.items():
            self.assertEqual(getattr(self.user, field_name), original_value)
        self.assertTrue(self.user.check_password("Strong-Pass-2026!"))
        self.assertEqual(self.subscription.pk, subscription_id)
        self.assertEqual(self.subscription.user_id, self.user.pk)
        self.assertEqual(self.subscription.sub_name, "Demo trial")
        self.assertEqual(self.notification.pk, notification_id)
        self.assertEqual(self.notification.sub_id, self.subscription.pk)
        self.assertEqual(self.notification.notif_title, "Demo reminder")
