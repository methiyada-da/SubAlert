import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings


LINE_TOKEN_URL = "https://api.line.me/oauth2/v2.1/token"
LINE_PROFILE_URL = "https://api.line.me/v2/profile"
LINE_FRIENDSHIP_URL = "https://api.line.me/friendship/v1/status"
LINE_PUSH_MESSAGE_URL = "https://api.line.me/v2/bot/message/push"
MAX_RESPONSE_BYTES = 1024 * 1024


class LineAPIError(Exception):
    """A safe, non-secret error raised when communication with LINE fails."""


def _request_json(request):
    try:
        with urlopen(request, timeout=settings.LINE_HTTP_TIMEOUT) as response:
            payload = response.read(MAX_RESPONSE_BYTES)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise LineAPIError("ไม่สามารถติดต่อบริการ LINE ได้") from exc

    try:
        data = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LineAPIError("LINE ส่งข้อมูลตอบกลับไม่ถูกต้อง") from exc

    if not isinstance(data, dict):
        raise LineAPIError("LINE ส่งข้อมูลตอบกลับไม่ถูกต้อง")
    return data


def exchange_code_for_token(code):
    body = urlencode(
        {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.LINE_CALLBACK_URL,
            "client_id": settings.LINE_LOGIN_CHANNEL_ID,
            "client_secret": settings.LINE_LOGIN_CHANNEL_SECRET,
        }
    ).encode("utf-8")
    request = Request(
        LINE_TOKEN_URL,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    data = _request_json(request)
    access_token = data.get("access_token")
    if not isinstance(access_token, str) or not access_token:
        raise LineAPIError("LINE ไม่ได้ส่ง access token กลับมา")
    return access_token


def fetch_line_profile(access_token):
    request = Request(
        LINE_PROFILE_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        method="GET",
    )
    return _request_json(request)


def fetch_friendship_status(access_token):
    request = Request(
        LINE_FRIENDSHIP_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        method="GET",
    )
    data = _request_json(request)
    friend_flag = data.get("friendFlag")
    if not isinstance(friend_flag, bool):
        raise LineAPIError("LINE ส่งสถานะการเพิ่มเพื่อนไม่ถูกต้อง")
    return friend_flag


def send_line_push_message(line_user_id, text):
    access_token = settings.LINE_MESSAGING_CHANNEL_ACCESS_TOKEN
    if not access_token:
        raise LineAPIError("ระบบยังไม่ได้ตั้งค่า LINE Messaging API")

    body = json.dumps(
        {
            "to": line_user_id,
            "messages": [
                {
                    "type": "text",
                    "text": text,
                }
            ],
        },
        ensure_ascii=False,
    ).encode("utf-8")
    request = Request(
        LINE_PUSH_MESSAGE_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    _request_json(request)
