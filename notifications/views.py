from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .models import Notification


@login_required
@require_POST
def mark_all_read(request):
    Notification.objects.filter(
        sub__user=request.user,
        notif_channel="WEB",
        notif_read=False,
    ).update(notif_read=True)

    next_url = request.POST.get("next", "")
    if not url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        next_url = reverse("dashboard:index")
    return redirect(next_url)
