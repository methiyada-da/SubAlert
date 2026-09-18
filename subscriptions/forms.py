from datetime import timedelta

from django import forms

from .date_utils import add_billing_cycle
from .models import Subscription


class SubscriptionForm(forms.ModelForm):
    MODE_TRIAL = "trial"
    MODE_PAID = "paid"

    CYCLE_PRESET_MAP = {
        "weekly": (1, "week"),
        "monthly": (1, "month"),
        "quarterly": (3, "month"),
        "half_yearly": (6, "month"),
        "yearly": (1, "year"),
    }
    CATEGORY_PRESETS = (
        "บันเทิง",
        "เพลง",
        "ซอฟต์แวร์",
        "การศึกษา",
        "สุขภาพและฟิตเนส",
        "Cloud / Storage",
        "เกม",
        "ข่าว / สื่อ",
    )
    PLATFORM_PRESET_MAP = {
        "apple_app_store": "Apple App Store",
        "google_play_store": "Google Play Store",
        "website": "เว็บไซต์",
    }
    PAYMENT_METHOD_PRESET_MAP = {
        "credit_debit_card": "บัตรเครดิต / เดบิต",
        "bank_debit": "หักบัญชีธนาคารอัตโนมัติ",
        "mobile_banking": "โมบายแบงก์กิ้ง / โอนธนาคาร",
        "promptpay": "พร้อมเพย์ / QR Code",
        "truemoney": "TrueMoney Wallet",
        "paypal": "PayPal",
        "mobile_carrier": "เรียกเก็บผ่านเครือข่ายมือถือ",
    }
    PAYMENT_METHOD_ALIASES = {
        "บัตร": "credit_debit_card",
        "บัตรเครดิต": "credit_debit_card",
        "บัตรเดบิต": "credit_debit_card",
    }
    TRIAL_PRESET_DAYS = {"3": 3, "7": 7, "14": 14, "30": 30}
    BILLING_FIELDS = (
        "sub_price",
        "sub_cycle_value",
        "sub_cycle_unit",
        "sub_next",
        "pay_method",
    )

    service_mode = forms.ChoiceField(
        label="ประเภทบริการ",
        choices=(
            (MODE_TRIAL, "ทดลองใช้ฟรี"),
            (MODE_PAID, "สมัครสมาชิกแบบชำระเงิน"),
        ),
        widget=forms.RadioSelect,
        error_messages={"required": "กรุณาเลือกประเภทบริการ"},
    )
    billing_cycle_preset = forms.ChoiceField(
        label="รอบชำระเงิน",
        required=False,
        choices=(
            ("weekly", "รายสัปดาห์"),
            ("monthly", "รายเดือน"),
            ("quarterly", "ทุก 3 เดือน"),
            ("half_yearly", "ทุก 6 เดือน"),
            ("yearly", "รายปี"),
            ("custom", "กำหนดเอง"),
        ),
    )
    category_preset = forms.ChoiceField(
        label="หมวดหมู่",
        required=False,
        choices=(
            ("", "เลือกหมวดหมู่"),
            ("บันเทิง", "บันเทิง"),
            ("เพลง", "เพลง"),
            ("ซอฟต์แวร์", "ซอฟต์แวร์"),
            ("การศึกษา", "การศึกษา"),
            ("สุขภาพและฟิตเนส", "สุขภาพและฟิตเนส"),
            ("Cloud / Storage", "Cloud / Storage"),
            ("เกม", "เกม"),
            ("ข่าว / สื่อ", "ข่าว / สื่อ"),
            ("other", "อื่น ๆ"),
        ),
    )
    category_custom = forms.CharField(
        label="ระบุหมวดหมู่",
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={"placeholder": "ระบุหมวดหมู่"}),
        error_messages={"max_length": "หมวดหมู่ต้องไม่เกิน 50 ตัวอักษร"},
    )
    platform_preset = forms.ChoiceField(
        label="ช่องทางที่สมัครบริการ",
        required=False,
        choices=(
            ("", "เลือกช่องทางที่สมัคร"),
            ("apple_app_store", "Apple App Store"),
            ("google_play_store", "Google Play Store"),
            ("website", "เว็บไซต์"),
            ("other", "ช่องทางอื่น ๆ"),
        ),
        help_text=(
            "เลือกช่องทางที่คุณเริ่มทดลองหรือสมัครบริการ "
            "เช่น App Store หรือเว็บไซต์ (ไม่ใช่ชื่อบริการ)"
        ),
    )
    platform_custom = forms.CharField(
        label="ระบุช่องทางที่สมัคร",
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={"placeholder": "เช่น สมัครผ่านพนักงานขาย"}),
        error_messages={
            "max_length": "ช่องทางที่สมัครต้องไม่เกิน 50 ตัวอักษร",
        },
    )
    payment_method_preset = forms.ChoiceField(
        label="วิธีชำระเงิน",
        required=False,
        choices=(
            ("", "เลือกวิธีชำระเงิน"),
            ("credit_debit_card", "บัตรเครดิต / เดบิต"),
            ("bank_debit", "หักบัญชีธนาคารอัตโนมัติ"),
            ("mobile_banking", "โมบายแบงก์กิ้ง / โอนธนาคาร"),
            ("promptpay", "พร้อมเพย์ / QR Code"),
            ("truemoney", "TrueMoney Wallet"),
            ("paypal", "PayPal"),
            ("mobile_carrier", "เรียกเก็บผ่านเครือข่ายมือถือ"),
            ("other", "อื่น ๆ"),
        ),
    )
    payment_method_custom = forms.CharField(
        label="ระบุวิธีชำระเงิน",
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={"placeholder": "ระบุวิธีชำระเงิน"}),
        error_messages={
            "max_length": "วิธีชำระเงินต้องไม่เกิน 50 ตัวอักษร",
        },
    )
    trial_duration_preset = forms.ChoiceField(
        label="ระยะเวลาทดลองใช้",
        required=False,
        choices=(
            ("3", "3 วัน"),
            ("7", "7 วัน"),
            ("14", "14 วัน"),
            ("30", "30 วัน"),
            ("custom", "กำหนดเอง"),
        ),
    )
    trial_custom_days = forms.IntegerField(
        label="จำนวนวันทดลองใช้ฟรี",
        required=False,
        min_value=1,
        widget=forms.NumberInput(attrs={"min": "1", "placeholder": "จำนวนวัน"}),
        error_messages={
            "invalid": "กรุณากรอกจำนวนวันเป็นตัวเลข",
            "min_value": "จำนวนวันทดลองใช้ฟรีต้องไม่น้อยกว่า 1 วัน",
        },
    )

    class Meta:
        model = Subscription
        fields = (
            "sub_name",
            "sub_plan",
            "sub_category",
            "sub_price",
            "sub_cycle_value",
            "sub_cycle_unit",
            "sub_platform",
            "pay_method",
            "sub_start",
            "sub_next",
            "trial_status",
            "trial_end",
            "alert_day",
            "sub_status",
            "sub_url",
        )
        labels = {
            "sub_name": "ชื่อบริการ",
            "sub_plan": "แพ็กเกจ",
            "sub_category": "หมวดหมู่",
            "sub_price": "ราคา",
            "sub_cycle_value": "ชำระทุก",
            "sub_cycle_unit": "หน่วยรอบชำระ",
            "sub_platform": "ช่องทางที่สมัครบริการ",
            "pay_method": "วิธีชำระเงิน",
            "sub_start": "วันที่เริ่มใช้งาน",
            "sub_next": "วันที่ชำระครั้งถัดไป",
            "trial_end": "วันสิ้นสุดช่วงทดลองใช้ฟรี",
            "alert_day": "แจ้งเตือนล่วงหน้า",
            "sub_status": "เปิดใช้งานการแจ้งเตือน",
            "sub_url": "ลิงก์เว็บไซต์ที่สมัครบริการ",
        }
        help_texts = {
            "sub_next": "ระบบช่วยคำนวณให้ แต่คุณสามารถแก้ไขวันที่เองได้",
            "alert_day": "จำนวนวันก่อนถึงกำหนดที่ต้องการรับแจ้งเตือน",
            "sub_status": (
                "ปิดเมื่อต้องการหยุดรับการแจ้งเตือน "
                "โดยรายการนี้จะยังถูกเก็บไว้และไม่ถูกลบ"
            ),
            "sub_url": "กรอกเมื่อต้องการเก็บลิงก์หน้าที่ใช้สมัครหรือจัดการบริการ",
        }
        widgets = {
            "sub_name": forms.TextInput(attrs={"placeholder": "เช่น แอปอ่านหนังสือ"}),
            "sub_plan": forms.TextInput(attrs={"placeholder": "เช่น Pro,Premium"}),
            "sub_category": forms.HiddenInput(),
            "sub_price": forms.NumberInput(attrs={"min": "0", "step": "0.01"}),
            "sub_cycle_value": forms.NumberInput(attrs={"min": "1"}),
            "sub_platform": forms.HiddenInput(),
            "pay_method": forms.HiddenInput(),
            "sub_start": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "sub_next": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "trial_status": forms.HiddenInput(),
            "trial_end": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "alert_day": forms.NumberInput(attrs={"min": "0"}),
            "sub_url": forms.URLInput(attrs={"placeholder": "https://example.com"}),
        }

    def __init__(self, *args, force_service_mode=None, **kwargs):
        self.force_service_mode = force_service_mode
        super().__init__(*args, **kwargs)

        for field_name in self.BILLING_FIELDS:
            self.fields[field_name].required = False
        self.fields["trial_end"].required = False

        if self.force_service_mode:
            self.fields["service_mode"].required = False
            self.fields["service_mode"].widget = forms.HiddenInput()

        self.fields["sub_price"].error_messages.update(
            {
                "invalid": "กรุณากรอกราคาเป็นตัวเลข",
                "min_value": "ราคาต้องไม่น้อยกว่า 0",
            }
        )
        self.fields["sub_cycle_value"].error_messages.update(
            {
                "invalid": "กรุณากรอกจำนวนรอบเป็นตัวเลข",
                "min_value": "จำนวนรอบชำระต้องไม่น้อยกว่า 1",
            }
        )
        self.fields["sub_start"].error_messages.update(
            {
                "required": "กรุณาระบุวันที่เริ่มใช้งาน",
                "invalid": "กรุณาระบุวันที่เริ่มใช้งานให้ถูกต้อง",
            }
        )
        self.fields["sub_next"].error_messages.update(
            {"invalid": "กรุณาระบุวันที่ชำระครั้งถัดไปให้ถูกต้อง"}
        )
        self.fields["trial_end"].error_messages.update(
            {"invalid": "กรุณาระบุวันสิ้นสุดช่วงทดลองใช้ฟรีให้ถูกต้อง"}
        )

        if not self.is_bound:
            self._set_initial_helper_values()

    def _set_initial_helper_values(self):
        is_existing = bool(self.instance and self.instance.pk)
        mode = (
            self.MODE_TRIAL
            if is_existing and self.instance.trial_status
            else self.MODE_PAID
            if is_existing
            else self.MODE_TRIAL
        )
        if self.force_service_mode:
            mode = self.force_service_mode

        self.initial["service_mode"] = mode
        self.initial["trial_status"] = mode == self.MODE_TRIAL

        current_cycle = (
            self.instance.sub_cycle_value,
            self.instance.sub_cycle_unit,
        )
        cycle_preset = next(
            (
                preset
                for preset, cycle in self.CYCLE_PRESET_MAP.items()
                if cycle == current_cycle
            ),
            "custom" if all(current_cycle) else "monthly",
        )
        self.initial["billing_cycle_preset"] = cycle_preset

        category = self.instance.sub_category
        if category in self.CATEGORY_PRESETS:
            self.initial["category_preset"] = category
        elif category:
            self.initial["category_preset"] = "other"
            self.initial["category_custom"] = category

        platform = self.instance.sub_platform
        platform_preset = next(
            (
                preset
                for preset, stored_value in self.PLATFORM_PRESET_MAP.items()
                if stored_value == platform
            ),
            "other" if platform else "",
        )
        self.initial["platform_preset"] = platform_preset
        if platform_preset == "other":
            self.initial["platform_custom"] = platform

        payment_method = self.instance.pay_method
        payment_preset = next(
            (
                preset
                for preset, stored_value in self.PAYMENT_METHOD_PRESET_MAP.items()
                if stored_value == payment_method
            ),
            self.PAYMENT_METHOD_ALIASES.get(
                payment_method,
                "other" if payment_method else "",
            ),
        )
        self.initial["payment_method_preset"] = payment_preset
        if payment_preset == "other":
            self.initial["payment_method_custom"] = payment_method

        self.initial.setdefault("trial_duration_preset", "7")
        if is_existing and self.instance.trial_end and self.instance.sub_start:
            trial_days = (self.instance.trial_end - self.instance.sub_start).days
            if str(trial_days) in self.TRIAL_PRESET_DAYS:
                self.initial["trial_duration_preset"] = str(trial_days)
            elif trial_days >= 1:
                self.initial["trial_duration_preset"] = "custom"
                self.initial["trial_custom_days"] = trial_days

    def _clean_category(self, cleaned_data):
        category_preset = cleaned_data.get("category_preset")
        if category_preset == "other":
            category = (cleaned_data.get("category_custom") or "").strip()
            if not category:
                self.add_error("category_custom", "กรุณาระบุหมวดหมู่")
        else:
            category = category_preset or ""
        cleaned_data["sub_category"] = category

    def _clear_billing_data(self, cleaned_data):
        for field_name in self.BILLING_FIELDS:
            self._errors.pop(field_name, None)
        cleaned_data["sub_price"] = None
        cleaned_data["sub_cycle_value"] = None
        cleaned_data["sub_cycle_unit"] = None
        cleaned_data["sub_next"] = None
        cleaned_data["pay_method"] = ""

    def _clean_platform(self, cleaned_data):
        platform_preset = cleaned_data.get("platform_preset")
        if platform_preset == "other":
            platform = (cleaned_data.get("platform_custom") or "").strip()
            if not platform:
                self.add_error("platform_custom", "กรุณาระบุช่องทางที่สมัคร")
        else:
            platform = self.PLATFORM_PRESET_MAP.get(platform_preset, "")

        cleaned_data["sub_platform"] = platform
        if platform_preset != "website":
            self._errors.pop("sub_url", None)
            cleaned_data["sub_url"] = ""

    def _get_trial_days(self, cleaned_data):
        preset = cleaned_data.get("trial_duration_preset")
        if preset in self.TRIAL_PRESET_DAYS:
            return self.TRIAL_PRESET_DAYS[preset]
        if preset == "custom":
            days = cleaned_data.get("trial_custom_days")
            if days is None:
                self.add_error(
                    "trial_custom_days",
                    "กรุณาระบุจำนวนวันทดลองใช้ฟรี",
                )
            return days
        return None

    def _clean_payment_method(self, cleaned_data):
        preset = cleaned_data.get("payment_method_preset")
        if preset in self.PAYMENT_METHOD_PRESET_MAP:
            payment_method = self.PAYMENT_METHOD_PRESET_MAP[preset]
        elif preset == "other":
            payment_method = (
                cleaned_data.get("payment_method_custom") or ""
            ).strip()
            if not payment_method:
                self.add_error(
                    "payment_method_custom",
                    "กรุณาระบุวิธีชำระเงิน",
                )
        else:
            payment_method = ""
            self.add_error(
                "payment_method_preset",
                "กรุณาเลือกวิธีชำระเงิน",
            )
        cleaned_data["pay_method"] = payment_method

    def _clean_trial_mode(self, cleaned_data):
        self._clear_billing_data(cleaned_data)
        cleaned_data["trial_status"] = True

        sub_start = cleaned_data.get("sub_start")
        trial_end = cleaned_data.get("trial_end")
        if not trial_end:
            trial_days = self._get_trial_days(cleaned_data)
            if sub_start and trial_days:
                trial_end = sub_start + timedelta(days=trial_days)
                cleaned_data["trial_end"] = trial_end

    def _clean_paid_cycle(self, cleaned_data):
        preset = cleaned_data.get("billing_cycle_preset")
        if preset in self.CYCLE_PRESET_MAP:
            cycle_value, cycle_unit = self.CYCLE_PRESET_MAP[preset]
            cleaned_data["sub_cycle_value"] = cycle_value
            cleaned_data["sub_cycle_unit"] = cycle_unit
            return cycle_value, cycle_unit

        cycle_value = cleaned_data.get("sub_cycle_value")
        cycle_unit = cleaned_data.get("sub_cycle_unit")
        if preset == "custom":
            if cycle_value is None:
                self.add_error("sub_cycle_value", "กรุณาระบุจำนวนรอบชำระ")
            if not cycle_unit:
                self.add_error("sub_cycle_unit", "กรุณาเลือกหน่วยรอบชำระ")
        else:
            self.add_error("billing_cycle_preset", "กรุณาเลือกรอบชำระเงิน")
        return cycle_value, cycle_unit

    def _clean_paid_mode(self, cleaned_data):
        cleaned_data["trial_status"] = False
        cleaned_data["trial_end"] = None

        cycle_value, cycle_unit = self._clean_paid_cycle(cleaned_data)
        sub_start = cleaned_data.get("sub_start")
        sub_next = cleaned_data.get("sub_next")
        if not sub_next and sub_start and cycle_value and cycle_unit:
            cleaned_data["sub_next"] = add_billing_cycle(
                sub_start,
                cycle_value,
                cycle_unit,
            )

        self._clean_payment_method(cleaned_data)

    def clean(self):
        cleaned_data = super().clean()
        mode = self.force_service_mode or cleaned_data.get("service_mode")
        cleaned_data["service_mode"] = mode
        self._clean_category(cleaned_data)
        self._clean_platform(cleaned_data)

        if mode == self.MODE_TRIAL:
            self._clean_trial_mode(cleaned_data)
        elif mode == self.MODE_PAID:
            self._clean_paid_mode(cleaned_data)

        return cleaned_data
