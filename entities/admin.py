from django.contrib import admin
from .models import Donor, Beneficiary, DonorContact


class DonorContactInline(admin.TabularInline):
    model = DonorContact
    extra = 1


@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):
    list_display = ('name_ar', 'created_at')
    search_fields = ('name_ar',)
    inlines = [DonorContactInline]


@admin.register(Beneficiary)
class BeneficiaryAdmin(admin.ModelAdmin):
    list_display = ('name_ar', 'type', 'created_at')
    list_filter = ('type',)
    search_fields = ('name_ar',)