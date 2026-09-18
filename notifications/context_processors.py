from django.utils import timezone

from .models import Notification


def topbar_notifications(request):
    if not request.user.is_authenticated:
        return {
            "topbar_notifications": [],
            "topbar_unread_count": 0,
        }

    notifications = Notification.objects.filter(
        sub__user=request.user,
        notif_channel="WEB",
        notif_date__lte=timezone.now(),
    ).select_related("sub").order_by("-notif_date", "-notif_id")

    return {
        "topbar_notifications": notifications[:5],
        "topbar_unread_count": notifications.filter(notif_read=False).count(),
    }
