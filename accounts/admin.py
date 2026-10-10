from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Role, User


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # نضيف حقولنا الخاصة (role, phone, donor, beneficiary) لشاشة التعديل
    fieldsets = BaseUserAdmin.fieldsets + (
        ("بيانات إضافية", {"fields": ("role", "phone", "donor", "beneficiary")}),
    )
    # ونضيفها أيضاً لشاشة "إضافة مستخدم جديد"
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("بيانات إضافية", {"fields": ("role", "phone", "donor", "beneficiary")}),
    )
    list_display = ("username", "email", "role", "is_staff")
    list_filter = ("role", "is_staff", "is_active")