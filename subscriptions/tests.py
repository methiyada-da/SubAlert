from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from .date_utils import add_billing_cycle
from .forms import SubscriptionForm
from .models import Subscription


class SubscriptionValidationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username="subscriber")

    def paid_data(self, **overrides):
        data = {
            "sub_name": "Example",
            "sub_price": 100,
            "sub_cycle_value": 1,
            "sub_cycle_unit": "month",
            "sub_start": date(2026, 1, 1),
            "sub_next": date(2026, 2, 1),
            "pay_method": "บัตรเครดิต",
            "user": self.user,
        }
        data.update(overrides)
        return data

    def test_trial_only_without_billing_is_valid(self):
        subscription = Subscription(
            sub_name="Free trial",
            sub_start=date(2026, 1, 1),
            trial_status=True,
            trial_end=date(2026, 1, 8),
            user=self.user,
        )
        subscription.full_clean()

    def test_trial_requires_end_date_not_before_start(self):
        missing_end = Subscription(
            sub_name="Trial",
            sub_start=date(2026, 1, 1),
            trial_status=True,
            user=self.user,
        )
        invalid_end = Subscription(
            sub_name="Trial",
            sub_start=date(2026, 1, 2),
            trial_status=True,
            trial_end=date(2026, 1, 1),
            user=self.user,
        )
        with self.assertRaises(ValidationError):
            missing_end.full_clean()
        with self.assertRaises(ValidationError):
            invalid_end.full_clean()

    def test_paid_mode_requires_billing_fields(self):
        subscription = Subscription(
            sub_name="Paid",
            sub_start=date(2026, 1, 1),
            trial_status=False,
            user=self.user,
        )
        with self.assertRaises(ValidationError) as context:
            subscription.full_clean()
        for field in ("sub_price", "sub_cycle_value", "sub_cycle_unit", "sub_next", "pay_method"):
            self.assertIn(field, context.exception.message_dict)

    def test_cycle_value_zero_and_negative_price_fail_validation(self):
        for overrides in ({"sub_cycle_value": 0}, {"sub_price": -1}):
            with self.subTest(overrides=overrides), self.assertRaises(ValidationError):
                Subscription(**self.paid_data(**overrides)).full_clean()

    def test_database_constraints_allow_null_but_reject_invalid_values(self):
        Subscription.objects.create(
            sub_name="Trial",
            sub_start=date(2026, 1, 1),
            trial_status=True,
            trial_end=date(2026, 1, 8),
            user=self.user,
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            Subscription.objects.create(**self.paid_data(sub_cycle_value=0))
        with self.assertRaises(IntegrityError), transaction.atomic():
            Subscription.objects.create(**self.paid_data(sub_price=-1))


class SubscriptionFormTests(TestCase):
    def paid_form_data(self, **overrides):
        data = {
            "service_mode": "paid",
            "sub_name": "Netflix",
            "sub_plan": "Premium",
            "category_preset": "บันเทิง",
            "category_custom": "",
            "sub_price": "419.00",
            "billing_cycle_preset": "monthly",
            "sub_cycle_value": "1",
            "sub_cycle_unit": "month",
            "platform_preset": "website",
            "platform_custom": "",
            "payment_method_preset": "credit_debit_card",
            "payment_method_custom": "",
            "pay_method": "บัตรเครดิต",
            "sub_start": "2026-01-01",
            "sub_next": "2026-02-01",
            "trial_duration_preset": "7",
            "trial_custom_days": "",
            "trial_end": "",
            "alert_day": "3",
            "sub_status": "on",
            "sub_url": "https://example.com",
        }
        data.update(overrides)
        return data

    def trial_form_data(self, **overrides):
        data = {
            "service_mode": "trial",
            "sub_name": "ทดลองแอป",
            "sub_start": "2026-01-01",
            "trial_duration_preset": "7",
            "trial_custom_days": "",
            "trial_end": "",
            "alert_day": "2",
            "sub_status": "on",
            "category_preset": "",
        }
        data.update(overrides)
        return data

    def test_trial_mode_accepts_minimal_data_and_clears_billing(self):
        form = SubscriptionForm(data=self.trial_form_data())
        self.assertTrue(form.is_valid(), form.errors)
        self.assertTrue(form.cleaned_data["trial_status"])
        self.assertEqual(form.cleaned_data["trial_end"], date(2026, 1, 8))
        for field in ("sub_price", "sub_cycle_value", "sub_cycle_unit", "sub_next"):
            self.assertIsNone(form.cleaned_data[field])
        self.assertEqual(form.cleaned_data["pay_method"], "")

    def test_trial_mode_ignores_invalid_hidden_billing_values(self):
        form = SubscriptionForm(data=self.trial_form_data(sub_price="-20", sub_cycle_value="0"))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertIsNone(form.cleaned_data["sub_price"])
        self.assertIsNone(form.cleaned_data["sub_cycle_value"])

    def test_trial_accepts_manual_end_and_validates_dates(self):
        valid = SubscriptionForm(data=self.trial_form_data(
            trial_duration_preset="custom", trial_end="2026-01-20"
        ))
        invalid = SubscriptionForm(data=self.trial_form_data(trial_end="2025-12-31"))
        self.assertTrue(valid.is_valid(), valid.errors)
        self.assertEqual(valid.cleaned_data["trial_end"], date(2026, 1, 20))
        self.assertFalse(invalid.is_valid())
        self.assertIn("trial_end", invalid.errors)

    def test_trial_requires_duration_or_end(self):
        form = SubscriptionForm(data=self.trial_form_data(
            trial_duration_preset="custom", trial_custom_days="", trial_end=""
        ))
        self.assertFalse(form.is_valid())
        self.assertIn("trial_custom_days", form.errors)
        self.assertIn("trial_end", form.errors)

    def test_paid_mode_requires_billing_fields(self):
        form = SubscriptionForm(data=self.paid_form_data(
            sub_price="", billing_cycle_preset="custom", sub_cycle_value="",
            sub_cycle_unit="", sub_next="", payment_method_preset="", pay_method=""
        ))
        self.assertFalse(form.is_valid())
        for field in ("sub_price", "sub_cycle_value", "sub_cycle_unit", "sub_next", "payment_method_preset"):
            self.assertIn(field, form.errors)

    def test_paid_mode_calculates_calendar_aware_next_date(self):
        form = SubscriptionForm(data=self.paid_form_data(
            sub_start="2028-01-31", sub_next="", billing_cycle_preset="monthly"
        ))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertFalse(form.cleaned_data["trial_status"])
        self.assertIsNone(form.cleaned_data["trial_end"])
        self.assertEqual(form.cleaned_data["sub_next"], date(2028, 2, 29))

    def test_paid_next_date_cannot_be_before_start(self):
        form = SubscriptionForm(data=self.paid_form_data(sub_next="2025-12-31"))
        self.assertFalse(form.is_valid())
        self.assertIn("sub_next", form.errors)

    def test_cycle_presets_and_custom_values_map_to_model_fields(self):
        presets = {
            "weekly": (1, "week"), "monthly": (1, "month"),
            "quarterly": (3, "month"), "half_yearly": (6, "month"),
            "yearly": (1, "year"),
        }
        for preset, expected in presets.items():
            with self.subTest(preset=preset):
                form = SubscriptionForm(data=self.paid_form_data(
                    billing_cycle_preset=preset, sub_cycle_value="99", sub_cycle_unit="day"
                ))
                self.assertTrue(form.is_valid(), form.errors)
                self.assertEqual((form.cleaned_data["sub_cycle_value"], form.cleaned_data["sub_cycle_unit"]), expected)
        for value, unit in ((45, "day"), (2, "week"), (18, "month")):
            with self.subTest(value=value, unit=unit):
                form = SubscriptionForm(data=self.paid_form_data(
                    billing_cycle_preset="custom", sub_cycle_value=str(value), sub_cycle_unit=unit
                ))
                self.assertTrue(form.is_valid(), form.errors)

    def test_category_mapping_and_user_field(self):
        preset = SubscriptionForm(data=self.trial_form_data(category_preset="เพลง"))
        custom = SubscriptionForm(data=self.trial_form_data(
            category_preset="other", category_custom="บริการเฉพาะทาง"
        ))
        self.assertTrue(preset.is_valid(), preset.errors)
        self.assertTrue(custom.is_valid(), custom.errors)
        self.assertEqual(preset.cleaned_data["sub_category"], "เพลง")
        self.assertEqual(custom.cleaned_data["sub_category"], "บริการเฉพาะทาง")
        self.assertNotIn("user", SubscriptionForm().fields)

    def test_platform_mapping_controls_website_url(self):
        website = SubscriptionForm(data=self.trial_form_data(
            platform_preset="website",
            sub_url="https://example.com/signup",
        ))
        app_store = SubscriptionForm(data=self.trial_form_data(
            platform_preset="apple_app_store",
            sub_url="https://example.com/should-be-cleared",
        ))
        custom = SubscriptionForm(data=self.trial_form_data(
            platform_preset="other",
            platform_custom="สมัครผ่านพนักงานขาย",
        ))

        self.assertTrue(website.is_valid(), website.errors)
        self.assertTrue(app_store.is_valid(), app_store.errors)
        self.assertTrue(custom.is_valid(), custom.errors)
        self.assertEqual(website.cleaned_data["sub_platform"], "เว็บไซต์")
        self.assertEqual(website.cleaned_data["sub_url"], "https://example.com/signup")
        self.assertEqual(app_store.cleaned_data["sub_platform"], "Apple App Store")
        self.assertEqual(app_store.cleaned_data["sub_url"], "")
        self.assertEqual(custom.cleaned_data["sub_platform"], "สมัครผ่านพนักงานขาย")

    def test_custom_platform_requires_a_value(self):
        form = SubscriptionForm(data=self.trial_form_data(
            platform_preset="other",
            platform_custom="",
        ))
        self.assertFalse(form.is_valid())
        self.assertIn("platform_custom", form.errors)

    def test_payment_method_preset_and_custom_value_map_to_existing_field(self):
        preset = SubscriptionForm(data=self.paid_form_data(
            payment_method_preset="promptpay",
            pay_method="ค่าที่ไม่ควรถูกใช้",
        ))
        custom = SubscriptionForm(data=self.paid_form_data(
            payment_method_preset="other",
            payment_method_custom="หักจากเงินเดือน",
        ))
        missing_custom = SubscriptionForm(data=self.paid_form_data(
            payment_method_preset="other",
            payment_method_custom="",
        ))

        self.assertTrue(preset.is_valid(), preset.errors)
        self.assertTrue(custom.is_valid(), custom.errors)
        self.assertEqual(preset.cleaned_data["pay_method"], "พร้อมเพย์ / QR Code")
        self.assertEqual(custom.cleaned_data["pay_method"], "หักจากเงินเดือน")
        self.assertFalse(missing_custom.is_valid())
        self.assertIn("payment_method_custom", missing_custom.errors)

    def test_edit_mode_initializes_service_and_cycle_modes(self):
        user = get_user_model().objects.create_user(username="edit-user")
        paid = Subscription.objects.create(
            sub_name="Custom", sub_price=100, sub_cycle_value=18,
            sub_cycle_unit="month", sub_start=date(2026, 1, 1),
            sub_next=date(2027, 7, 1), pay_method="บัตร", user=user,
        )
        trial = Subscription.objects.create(
            sub_name="Trial", sub_start=date(2026, 1, 1), trial_status=True,
            trial_end=date(2026, 1, 8), user=user,
        )
        self.assertEqual(SubscriptionForm(instance=paid).initial["service_mode"], "paid")
        self.assertEqual(SubscriptionForm(instance=paid).initial["billing_cycle_preset"], "custom")
        self.assertEqual(SubscriptionForm(instance=paid).initial["payment_method_preset"], "credit_debit_card")
        self.assertEqual(SubscriptionForm(instance=trial).initial["service_mode"], "trial")
        self.assertEqual(SubscriptionForm(instance=trial).initial["trial_duration_preset"], "7")


class BillingDateCalculationTests(SimpleTestCase):
    def test_month_end_and_leap_year_are_calendar_aware(self):
        self.assertEqual(add_billing_cycle(date(2028, 1, 31), 1, "month"), date(2028, 2, 29))
        self.assertEqual(add_billing_cycle(date(2027, 1, 31), 1, "month"), date(2027, 2, 28))
        self.assertEqual(add_billing_cycle(date(2028, 2, 29), 1, "year"), date(2029, 2, 28))


class SubscriptionWorkflowTests(TestCase):
    password = "Strong-Pass-2026!"

    @classmethod
    def setUpTestData(cls):
        users = get_user_model()
        cls.user = users.objects.create_user(username="owner", password=cls.password)
        cls.other_user = users.objects.create_user(username="other", password=cls.password)
        cls.trial = Subscription.objects.create(
            sub_name="Trial service", sub_start=date(2026, 1, 1),
            trial_status=True, trial_end=date(2026, 1, 8), user=cls.user,
        )
        cls.other_trial = Subscription.objects.create(
            sub_name="Private trial", sub_start=date(2026, 1, 1),
            trial_status=True, trial_end=date(2026, 1, 8), user=cls.other_user,
        )

    def paid_data(self, **overrides):
        data = {
            "service_mode": "paid", "sub_name": "Trial service",
            "sub_plan": "Premium", "category_preset": "ซอฟต์แวร์",
            "platform_preset": "apple_app_store", "platform_custom": "",
            "payment_method_preset": "credit_debit_card",
            "payment_method_custom": "",
            "sub_price": "250.00", "billing_cycle_preset": "monthly",
            "sub_cycle_value": "1", "sub_cycle_unit": "month",
            "pay_method": "บัตรเครดิต", "sub_start": "2026-01-01",
            "sub_next": "2026-02-01", "alert_day": "3", "sub_status": "on",
        }
        data.update(overrides)
        return data

    def trial_data(self, **overrides):
        data = {
            "service_mode": "trial", "sub_name": "New trial",
            "sub_start": "2026-03-01", "trial_duration_preset": "14",
            "trial_end": "", "alert_day": "2", "sub_status": "on",
            "category_preset": "",
        }
        data.update(overrides)
        return data

    def setUp(self):
        self.client.force_login(self.user)

    def test_create_page_has_two_thai_modes_and_helpers(self):
        response = self.client.get(reverse("subscriptions:create"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ทดลองใช้ฟรี")
        self.assertContains(response, "สมัครสมาชิกแบบชำระเงิน")
        self.assertContains(response, "เพิ่มบริการ")
        self.assertContains(response, "ไม่ใช่ชื่อบริการ")
        self.assertContains(response, "Apple App Store")
        self.assertContains(response, "Google Play Store")
        self.assertContains(response, "เปิดใช้งานการแจ้งเตือน")
        self.assertContains(response, "รายการนี้จะยังถูกเก็บไว้และไม่ถูกลบ")
        self.assertContains(response, 'id="app-sidebar"')
        self.assertContains(response, "js/subscription_form.js")
        self.assertContains(response, "จำเป็นต้องระบุ โดยบางช่องระบบจะคำนวณค่าเริ่มต้นให้")
        self.assertContains(response, 'class="required-mark"', count=16)

    def test_subscription_list_uses_card_page_with_search_and_filters(self):
        response = self.client.get(reverse("subscriptions:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "การสมัครบริการของฉัน")
        self.assertContains(response, 'id="service-filters"')
        self.assertContains(response, 'id="global-service-search"')
        self.assertContains(response, self.trial.sub_name)
        self.assertNotContains(response, self.other_trial.sub_name)

    def test_subscription_list_filters_mode_and_search_server_side(self):
        paid = Subscription.objects.create(
            sub_name="Paid music",
            sub_category="เพลง",
            sub_price=99,
            sub_cycle_value=1,
            sub_cycle_unit="month",
            sub_start=date(2026, 1, 1),
            sub_next=date(2026, 2, 1),
            pay_method="บัตรเครดิต",
            user=self.user,
        )

        paid_response = self.client.get(reverse("subscriptions:list"), {"mode": "paid"})
        search_response = self.client.get(reverse("subscriptions:list"), {"q": "music"})

        for response in (paid_response, search_response):
            self.assertContains(response, paid.sub_name)
            self.assertNotContains(response, self.trial.sub_name)

    def test_categories_are_not_created_as_main_filter_chips(self):
        custom_category = "แอปทั่วไป"
        preset_category = "การศึกษา"
        self.trial.sub_category = preset_category
        self.trial.save(update_fields=["sub_category"])
        Subscription.objects.create(
            sub_name="Custom category trial",
            sub_category=custom_category,
            sub_start=date(2026, 1, 1),
            trial_status=True,
            trial_end=date(2026, 1, 8),
            user=self.user,
        )

        response = self.client.get(reverse("subscriptions:list"))

        self.assertContains(response, custom_category)
        self.assertContains(response, preset_category)
        self.assertNotContains(response, f"?category={custom_category}")
        self.assertNotContains(response, f"?category={preset_category}")
        self.assertContains(response, 'class="filter-chip', count=3)

    def test_create_trial_only_assigns_owner_without_fake_billing(self):
        response = self.client.post(reverse("subscriptions:create"), self.trial_data(user=self.other_user.pk))
        created = Subscription.objects.get(sub_name="New trial")
        self.assertRedirects(response, reverse("subscriptions:list"))
        self.assertEqual(created.user, self.user)
        self.assertTrue(created.trial_status)
        self.assertEqual(created.trial_end, date(2026, 3, 15))
        self.assertIsNone(created.sub_price)
        self.assertIsNone(created.sub_cycle_value)
        self.assertIsNone(created.sub_cycle_unit)
        self.assertIsNone(created.sub_next)
        self.assertEqual(created.pay_method, "")

    def test_conversion_updates_same_record_and_activates_it(self):
        self.trial.sub_status = False
        self.trial.save(update_fields=["sub_status"])
        original_count = Subscription.objects.count()
        response = self.client.post(
            reverse("subscriptions:continue_paid", args=[self.trial.sub_id]),
            self.paid_data(sub_status=""),
        )
        self.assertRedirects(response, reverse("subscriptions:detail", args=[self.trial.sub_id]))
        self.trial.refresh_from_db()
        self.assertEqual(Subscription.objects.count(), original_count)
        self.assertFalse(self.trial.trial_status)
        self.assertIsNone(self.trial.trial_end)
        self.assertTrue(self.trial.sub_status)
        self.assertEqual(self.trial.sub_price, 250)
        self.assertEqual(self.trial.sub_cycle_value, 1)
        self.assertEqual(self.trial.sub_cycle_unit, "month")

    def test_conversion_page_is_paid_only_and_owner_scoped(self):
        response = self.client.get(reverse("subscriptions:continue_paid", args=[self.trial.sub_id]))
        forbidden = self.client.get(reverse("subscriptions:continue_paid", args=[self.other_trial.sub_id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "เปลี่ยนจากทดลองใช้ฟรีเป็นแบบชำระเงิน")
        self.assertContains(response, 'name="service_mode"', html=False)
        self.assertEqual(forbidden.status_code, 404)

    def test_deactivate_is_post_only_owner_scoped(self):
        url = reverse("subscriptions:deactivate", args=[self.trial.sub_id])
        self.assertEqual(self.client.get(url).status_code, 405)
        response = self.client.post(url)
        self.assertRedirects(response, reverse("subscriptions:detail", args=[self.trial.sub_id]))
        self.trial.refresh_from_db()
        self.assertFalse(self.trial.sub_status)
        self.assertEqual(
            self.client.post(reverse("subscriptions:deactivate", args=[self.other_trial.sub_id])).status_code,
            404,
        )

    def test_detail_shows_trial_actions_without_billing_placeholders(self):
        response = self.client.get(reverse("subscriptions:detail", args=[self.trial.sub_id]))
        self.assertContains(response, "ใช้งานต่อแบบชำระเงิน")
        self.assertContains(response, "ไม่ใช้ต่อ / หยุดติดตาม")
        self.assertNotContains(response, "None บาท")

    def test_anonymous_and_other_user_access_is_protected(self):
        self.assertEqual(
            self.client.get(reverse("subscriptions:detail", args=[self.other_trial.sub_id])).status_code,
            404,
        )
        self.client.logout()
        response = self.client.get(reverse("subscriptions:list"))
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('subscriptions:list')}")

    def test_owner_can_delete_subscription(self):
        response = self.client.post(reverse("subscriptions:delete", args=[self.trial.sub_id]))
        self.assertRedirects(response, reverse("subscriptions:list"))
        self.assertFalse(Subscription.objects.filter(sub_id=self.trial.sub_id).exists())
