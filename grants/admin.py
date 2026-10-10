from django.contrib import admin
from .models import Grant, GrantItem, BeneficiaryCount, Visit, ImpactReport, GrantUpdate


@admin.register(Grant)
class GrantAdmin(admin.ModelAdmin):
    list_display = ('title_ar', 'donor', 'beneficiary', 'type', 'amount', 'status', 'grant_date')
    list_filter = ('type', 'status', 'grant_date')
    search_fields = ('title_ar',)
    autocomplete_fields = ('donor', 'beneficiary')


@admin.register(GrantItem)
class GrantItemAdmin(admin.ModelAdmin):
    list_display = ('item_type', 'serial_number', 'condition', 'grant')
    list_filter = ('condition',)
    search_fields = ('serial_number', 'item_type')
    autocomplete_fields = ('grant',)


@admin.register(BeneficiaryCount)
class BeneficiaryCountAdmin(admin.ModelAdmin):
    list_display = ('grant', 'category', 'count')
    list_filter = ('category',)
    autocomplete_fields = ('grant',)


@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = ('grant', 'visit_date')
    list_filter = ('visit_date',)
    autocomplete_fields = ('grant',)


@admin.register(ImpactReport)
class ImpactReportAdmin(admin.ModelAdmin):
    list_display = ('grant', 'stage', 'report_date', 'uploaded_by')
    list_filter = ('stage',)
    autocomplete_fields = ('grant',)


@admin.register(GrantUpdate)
class GrantUpdateAdmin(admin.ModelAdmin):
    list_display = ('title_ar', 'type', 'grant', 'created_at')
    list_filter = ('type',)
    search_fields = ('title_ar',)
    autocomplete_fields = ('grant',)