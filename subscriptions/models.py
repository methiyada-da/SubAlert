from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class Subscription(models.Model):
    CYCLE_UNIT_CHOICES = [
        ("day", "วัน"),
        ("week", "สัปดาห์"),
        ("month", "เดือน"),
        ("year", "ปี"),
    ]

    sub_id = models.AutoField(primary_key=True)

    sub_name = models.CharField(
        max_length=100
    )

    sub_plan = models.CharField(
        max_length=100,
        blank=True,
    )

    sub_category = models.CharField(
        max_length=50,
        blank=True,
    )

    sub_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
    )

    # เช่น
    # 1 เดือน = รายเดือน
    # 3 เดือน = ทุก 3 เดือน
    # 1 ปี = รายปี
    # 2 สัปดาห์ = ทุก 2 สัปดาห์
    sub_cycle_value = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        null=True,
        blank=True,
    )

    sub_cycle_unit = models.CharField(
        max_length=10,
        choices=CYCLE_UNIT_CHOICES,
        null=True,
        blank=True,
    )

    sub_platform = models.CharField(
        max_length=50,
        blank=True,
    )

    pay_method = models.CharField(
        max_length=50,
        blank=True,
    )

    sub_start = models.DateField()

    sub_next = models.DateField(
        null=True,
        blank=True,
    )

    trial_status = models.BooleanField(
        default=False
    )

    trial_end = models.DateField(
        null=True,
        blank=True,
    )

    alert_day = models.PositiveIntegerField(
        default=3
    )

    sub_status = models.BooleanField(
        default=True
    )

    sub_url = models.URLField(
        max_length=255,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscriptions",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(sub_price__gte=0),
                name="subscription_price_gte_0",
            ),
            models.CheckConstraint(
                condition=models.Q(sub_cycle_value__gte=1),
                name="subscription_cycle_value_gte_1",
            ),
        ]

    def clean(self):
        super().clean()
        errors = {}

        if self.trial_status:
            if not self.trial_end:
                errors["trial_end"] = "กรุณาระบุวันสิ้นสุดช่วงทดลองใช้ฟรี"
            elif self.sub_start and self.trial_end < self.sub_start:
                errors["trial_end"] = (
                    "วันสิ้นสุดช่วงทดลองใช้ฟรีต้องไม่อยู่ก่อนวันที่เริ่มใช้งาน"
                )
        else:
            required_billing_fields = {
                "sub_price": "กรุณากรอกราคา",
                "sub_cycle_value": "กรุณาระบุจำนวนรอบชำระ",
                "sub_cycle_unit": "กรุณาเลือกหน่วยรอบชำระ",
                "sub_next": "กรุณาระบุวันที่ชำระครั้งถัดไป",
                "pay_method": "กรุณาระบุวิธีชำระเงิน",
            }
            for field_name, message in required_billing_fields.items():
                if getattr(self, field_name) in (None, ""):
                    errors[field_name] = message

            if self.sub_start and self.sub_next and self.sub_next < self.sub_start:
                errors["sub_next"] = (
                    "วันที่ชำระครั้งถัดไปต้องไม่อยู่ก่อนวันที่เริ่มใช้งาน"
                )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return self.sub_name
