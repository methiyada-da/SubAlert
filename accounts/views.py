import base64
import hashlib
import hmac
import json
import secrets
from urllib.parse import quote, urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, UpdateView

from .forms import (
    LoginForm,
    ProfileForm,
    RegistrationForm,
    ThaiPasswordChangeForm,
)
from .line_login import (
    LineAPIError,
    exchange_code_for_token,
    fetch_friendship_status,
    fetch_line_profile,
    send_line_push_message,
)


LINE_AUTHORIZE_URL = "https://access.line.me/oauth2/v2.1/authorize"
LINE_OAUTH_STATE_SESSION_KEY = "line_oauth_state"
LINE_TEST_MESSAGE = (
    "🔔 ทดสอบการแจ้งเตือนจาก SubAlert\n"
    "การเชื่อมต่อ LINE พร้อมใช้งานแล้ว"
)


@csrf_exempt
@require_POST
def line_webhook(request):
    """Receive signed webhook events from the LINE Messaging API."""
    channel_secret = settings.LINE_MESSAGING_CHANNEL_SECRET
    received_signature = request.headers.get("x-line-signature", "")
    raw_body = request.body

    if not channel_secret or not received_signature:
        return HttpResponseBadRequest()

    expected_signature = base64.b64encode(
        hmac.new(
            channel_secret.encode("utf-8"),
            raw_body,
            hashlib.sha256,
        ).digest()
    ).decode("ascii")
    try:
        signature_is_valid = hmac.compare_digest(
            expected_signature,
            received_signature,
        )
    except TypeError:
        signature_is_valid = False
    if not signature_is_valid:
        return HttpResponseBadRequest()

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return HttpResponseBadRequest()

    if not isinstance(payload, dict):
        return HttpResponseBadRequest()

    events = payload.get("events", [])
    if not isinstance(events, list):
        return HttpResponseBadRequest()

    user_model = get_user_model()
    for event in events:
        if not isinstance(event, dict):
            continue

        event_type = event.get("type")
        if event_type not in {"follow", "unfollow"}:
            continue

        source = event.get("source")
        if not isinstance(source, dict):
            continue

        line_user_id = source.get("userId")
        if not isinstance(line_user_id, str) or not line_user_id:
            continue

        line_status = 2 if event_type == "follow" else 1
        user_model.objects.filter(line_id=line_user_id).update(
            line_status=line_status,
        )

    return HttpResponse(status=200)


def _line_settings_are_configured():
    return all(
        (
            settings.LINE_LOGIN_CHANNEL_ID,
            settings.LINE_LOGIN_CHANNEL_SECRET,
            settings.LINE_CALLBACK_URL,
        )
    )


@login_required
def line_connect(request):
    if not _line_settings_are_configured():
        messages.error(
            request,
            "ยังไม่สามารถเชื่อมต่อ LINE ได้ เนื่องจากระบบตั้งค่า LINE Login ไม่ครบ",
        )
        return redirect("accounts:profile")

    state = secrets.token_hex(32)
    request.session[LINE_OAUTH_STATE_SESSION_KEY] = state
    authorization_query = urlencode(
        {
            "response_type": "code",
            "client_id": settings.LINE_LOGIN_CHANNEL_ID,
            "redirect_uri": settings.LINE_CALLBACK_URL,
            "state": state,
            "scope": "openid profile",
            "bot_prompt": "aggressive",
        },
        quote_via=quote,
    )
    return redirect(f"{LINE_AUTHORIZE_URL}?{authorization_query}")


@login_required
def line_callback(request):
    expected_state = request.session.pop(LINE_OAUTH_STATE_SESSION_KEY, None)
    received_state = request.GET.get("state", "")
    if (
        not expected_state
        or not received_state
        or not secrets.compare_digest(expected_state, received_state)
    ):
        messages.error(
            request,
            "ไม่สามารถเชื่อมต่อ LINE ได้ เนื่องจากข้อมูลยืนยันไม่ถูกต้อง กรุณาลองใหม่",
        )
        return redirect("accounts:profile")

    if request.GET.get("error"):
        messages.warning(request, "ยกเลิกการเชื่อมต่อบัญชี LINE แล้ว")
        return redirect("accounts:profile")

    code = request.GET.get("code", "").strip()
    if not code:
        messages.error(request, "LINE ไม่ได้ส่งรหัสยืนยันกลับมา กรุณาลองใหม่")
        return redirect("accounts:profile")

    if not _line_settings_are_configured():
        messages.error(
            request,
            "ไม่สามารถเชื่อมต่อ LINE ได้ เนื่องจากระบบตั้งค่า LINE Login ไม่ครบ",
        )
        return redirect("accounts:profile")

    try:
        access_token = exchange_code_for_token(code)
        profile = fetch_line_profile(access_token)
    except LineAPIError:
        messages.error(
            request,
            "เชื่อมต่อกับ LINE ไม่สำเร็จ กรุณาตรวจสอบอินเทอร์เน็ตแล้วลองใหม่",
        )
        return redirect("accounts:profile")

    line_user_id = profile.get("userId")
    if isinstance(line_user_id, str):
        line_user_id = line_user_id.strip()
    if (
        not isinstance(line_user_id, str)
        or not line_user_id
        or line_user_id.startswith("@")
        or len(line_user_id) > 100
    ):
        messages.error(request, "LINE ไม่ได้ส่ง User ID ที่ถูกต้องกลับมา")
        return redirect("accounts:profile")
    if (
        get_user_model()
        .objects.filter(line_id=line_user_id)
        .exclude(pk=request.user.pk)
        .exists()
    ):
        messages.error(
            request,
            "บัญชี LINE นี้เชื่อมกับบัญชี SubAlert อื่นอยู่แล้ว",
        )
        return redirect("accounts:profile")

    line_status = 1
    try:
        if fetch_friendship_status(access_token):
            line_status = 2
    except LineAPIError:
        pass

    request.user.line_id = line_user_id
    request.user.line_status = line_status
    try:
        request.user.save(update_fields=["line_id", "line_status"])
    except IntegrityError:
        messages.error(
            request,
            "บัญชี LINE นี้เชื่อมกับบัญชี SubAlert อื่นอยู่แล้ว",
        )
        return redirect("accounts:profile")

    if line_status == 2:
        messages.success(
            request,
            "เชื่อมต่อ LINE สำเร็จ และพร้อมรับการแจ้งเตือนแล้ว",
        )
    else:
        messages.success(
            request,
            "เชื่อมต่อบัญชี LINE สำเร็จ แต่ยังไม่พร้อมรับการแจ้งเตือน",
        )
    return redirect("accounts:profile")


@login_required
@require_POST
def line_test_message(request):
    if not request.user.line_id or request.user.line_status != 2:
        messages.warning(request, "LINE ยังไม่พร้อมรับการแจ้งเตือน")
        return redirect("accounts:profile")

    try:
        send_line_push_message(request.user.line_id, LINE_TEST_MESSAGE)
    except LineAPIError:
        messages.error(
            request,
            "ส่งข้อความทดสอบไม่สำเร็จ กรุณาลองใหม่อีกครั้ง",
        )
    else:
        messages.success(request, "ส่งข้อความทดสอบเรียบร้อยแล้ว")
    return redirect("accounts:profile")


class RegisterView(CreateView):
    form_class = RegistrationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("accounts:login")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("dashboard:index")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "สมัครสมาชิกสำเร็จ กรุณาเข้าสู่ระบบ")
        return response


class AccountLoginView(LoginView):
    authentication_form = LoginForm
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "เข้าสู่ระบบสำเร็จ")
        return response


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    form_class = ProfileForm
    template_name = "accounts/profile.html"
    success_url = reverse_lazy("accounts:profile")

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        subscriptions = self.request.user.subscriptions.all()
        context["subscription_count"] = subscriptions.count()
        context["active_subscription_count"] = subscriptions.filter(
            sub_status=True,
        ).count()
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "บันทึกข้อมูลโปรไฟล์แล้ว")
        return response


class AccountPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    form_class = ThaiPasswordChangeForm
    template_name = "accounts/password_change.html"
    success_url = reverse_lazy("accounts:profile")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "เปลี่ยนรหัสผ่านสำเร็จ")
        return response
