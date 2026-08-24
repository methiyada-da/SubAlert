from django.contrib import admin

from .models import Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "sub_id",
        "sub_name",
        "sub_price",
        "sub_cycle_value",
        "sub_cycle_unit",
        "sub_next",
        "sub_status",
        "user",
    )

    search_fields = (
        "sub_name",
        "user__username",
    )