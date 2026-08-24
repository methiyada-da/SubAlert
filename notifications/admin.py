from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "notif_id",
        "notif_title",
        "notif_channel",
        "notif_date",
        "notif_status",
        "notif_read",
        "sub",
        "subscription_user",
    )

    list_select_related = (
        "sub",
        "sub__user",
    )

    @admin.display(ordering="sub__user", description="User")
    def subscription_user(self, obj):
        return obj.sub.user
