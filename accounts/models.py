from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    LINE_STATUS_CHOICES = [
        (0, "ยังไม่เชื่อมต่อ"),
        (1, "ผูกบัญชีแล้ว แต่ยังไม่แอดเพื่อนบอท"),
        (2, "ผูกบัญชีและแอดเพื่อนแล้ว"),
    ]

    line_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        unique=True,
    )

    line_status = models.IntegerField(
        choices=LINE_STATUS_CHOICES,
        default=0,
    )

    def save(self, *args, **kwargs):
        if self.line_id is not None:
            self.line_id = self.line_id.strip() or None
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username
