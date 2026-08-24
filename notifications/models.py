from django.db import models

from subscriptions.models import Subscription


class Notification(models.Model):
    CHANNEL_CHOICES = [
        ("WEB", "เว็บไซต์"),
        ("LINE", "LINE"),
    ]

    STATUS_CHOICES = [
        (0, "รอส่ง"),
        (1, "ส่งแล้ว"),
        (2, "ส่งไม่สำเร็จ"),
    ]

    notif_id = models.BigAutoField(
        primary_key=True
    )

    notif_type = models.CharField(
        max_length=30
    )

    notif_title = models.CharField(
        max_length=100
    )

    notif_text = models.CharField(
        max_length=255
    )

    notif_date = models.DateTimeField()

    notif_channel = models.CharField(
        max_length=10,
        choices=CHANNEL_CHOICES,
    )

    notif_url = models.CharField(
        max_length=255,
        blank=True,
    )

    notif_sent = models.DateTimeField(
        null=True,
        blank=True,
    )

    notif_status = models.IntegerField(
        choices=STATUS_CHOICES,
        default=0,
    )

    notif_read = models.BooleanField(
        default=False
    )

    sub = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    def __str__(self):
        return self.notif_title
