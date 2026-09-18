from django.contrib.auth.password_validation import (
    CommonPasswordValidator,
    MinimumLengthValidator,
    NumericPasswordValidator,
    UserAttributeSimilarityValidator,
)
from django.core.exceptions import ValidationError


class ThaiUserAttributeSimilarityValidator(UserAttributeSimilarityValidator):
    def validate(self, password, user=None):
        try:
            return super().validate(password, user)
        except ValidationError as error:
            raise ValidationError(
                "รหัสผ่านคล้ายกับข้อมูลส่วนตัวของคุณมากเกินไป",
                code="password_too_similar",
            ) from error

    def get_help_text(self):
        return "รหัสผ่านต้องไม่คล้ายกับข้อมูลส่วนตัวของคุณมากเกินไป"


class ThaiMinimumLengthValidator(MinimumLengthValidator):
    def validate(self, password, user=None):
        try:
            return super().validate(password, user)
        except ValidationError as error:
            raise ValidationError(
                f"รหัสผ่านสั้นเกินไป ต้องมีอย่างน้อย {self.min_length} ตัวอักษร",
                code="password_too_short",
                params={"min_length": self.min_length},
            ) from error

    def get_help_text(self):
        return f"รหัสผ่านต้องมีอย่างน้อย {self.min_length} ตัวอักษร"


class ThaiCommonPasswordValidator(CommonPasswordValidator):
    def validate(self, password, user=None):
        try:
            return super().validate(password, user)
        except ValidationError as error:
            raise ValidationError(
                "รหัสผ่านนี้เป็นรหัสผ่านที่ใช้กันทั่วไป กรุณาเลือกรหัสผ่านที่คาดเดายากขึ้น",
                code="password_too_common",
            ) from error

    def get_help_text(self):
        return "รหัสผ่านต้องไม่เป็นรหัสผ่านที่ใช้กันทั่วไป"


class ThaiNumericPasswordValidator(NumericPasswordValidator):
    def validate(self, password, user=None):
        try:
            return super().validate(password, user)
        except ValidationError as error:
            raise ValidationError(
                "รหัสผ่านต้องไม่เป็นตัวเลขทั้งหมด",
                code="password_entirely_numeric",
            ) from error

    def get_help_text(self):
        return "รหัสผ่านต้องไม่เป็นตัวเลขทั้งหมด"
