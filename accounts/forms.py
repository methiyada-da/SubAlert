from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(
        label="อีเมล",
        widget=forms.EmailInput(
            attrs={
                "autocomplete": "email",
                "placeholder": "name@example.com",
            }
        ),
    )

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = (
            "username",
            "email",
            "password1",
            "password2",
        )
        labels = {
            "username": "ชื่อผู้ใช้",
        }
        widgets = {
            "username": forms.TextInput(
                attrs={
                    "autocomplete": "username",
                    "placeholder": "ชื่อผู้ใช้",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].help_text = (
            "จำเป็นต้องกรอก ไม่เกิน 150 ตัวอักษร "
            "ใช้ได้เฉพาะตัวอักษร ตัวเลข และเครื่องหมาย @ . + - _"
        )
        self.fields["password1"].label = "รหัสผ่าน"
        self.fields["password2"].label = "ยืนยันรหัสผ่าน"
        self.fields["password1"].help_text = (
            "<ul>"
            "<li>รหัสผ่านต้องไม่คล้ายกับข้อมูลส่วนตัวอื่นมากเกินไป</li>"
            "<li>รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร</li>"
            "<li>รหัสผ่านต้องไม่เป็นรหัสผ่านที่ใช้กันทั่วไป</li>"
            "<li>รหัสผ่านต้องไม่เป็นตัวเลขทั้งหมด</li>"
            "</ul>"
        )
        self.fields["password2"].help_text = (
            "กรอกรหัสผ่านเดิมอีกครั้งเพื่อยืนยัน"
        )
        self.fields["password1"].widget.attrs.update(
            {"autocomplete": "new-password", "placeholder": "รหัสผ่าน"}
        )
        self.fields["password2"].widget.attrs.update(
            {"autocomplete": "new-password", "placeholder": "ยืนยันรหัสผ่าน"}
        )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        user_model = get_user_model()
        if user_model.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("อีเมลนี้ถูกใช้งานแล้ว")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="ชื่อผู้ใช้",
        widget=forms.TextInput(
            attrs={
                "autofocus": True,
                "autocomplete": "username",
                "placeholder": "ชื่อผู้ใช้",
            }
        ),
    )
    password = forms.CharField(
        label="รหัสผ่าน",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "current-password",
                "placeholder": "รหัสผ่าน",
            }
        ),
    )
