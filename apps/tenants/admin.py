from django.contrib import admin
from .models import (
    Tenant, TenantAdmin, EndUser, InfoSpot, Content, 
    SpotAccess, UserCredit, CreditPurchase, CreditTransaction
)


@admin.register(Tenant)
class TenantModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'subdomain', 'venue_type', 'is_active', 'created_at']
    list_filter = ['venue_type', 'is_active', 'created_at']
    search_fields = ['name', 'subdomain', 'contact_email']
    readonly_fields = ['created_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'subdomain', 'venue_type', 'contact_email', 'timezone', 'is_active')
        }),
        ('Branding', {
            'fields': ('logo', 'primary_color', 'secondary_color')
        }),
        ('Metadata', {
            'fields': ('created_at',)
        }),
    )


@admin.register(TenantAdmin)
class TenantAdminModelAdmin(admin.ModelAdmin):
    list_display = ['user', 'tenant', 'role', 'created_at']
    list_filter = ['role', 'created_at', 'tenant']
    search_fields = ['user__username', 'user__email', 'tenant__name']
    readonly_fields = ['created_at']


@admin.register(EndUser)
class EndUserAdmin(admin.ModelAdmin):
    list_display = ['user', 'preferred_language', 'phone_number', 'created_at']
    list_filter = ['preferred_language', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone_number']
    readonly_fields = ['created_at']


@admin.register(InfoSpot)
class InfoSpotAdmin(admin.ModelAdmin):
    list_display = ['name', 'tenant', 'access_type', 'credit_cost', 'is_active', 'created_at']
    list_filter = ['access_type', 'is_active', 'tenant', 'created_at']
    search_fields = ['name', 'description', 'tenant__name']
    readonly_fields = ['uuid', 'qr_code_data', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('tenant', 'name', 'description', 'location_description')
        }),
        ('Access Control', {
            'fields': ('access_type', 'credit_cost')
        }),
        ('Identifiers', {
            'fields': ('uuid', 'qr_code_data', 'nfc_tag_id')
        }),
        ('Status', {
            'fields': ('is_active', 'display_order')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = ['title', 'info_spot', 'language', 'version', 'created_at']
    list_filter = ['language', 'created_at', 'info_spot__tenant']
    search_fields = ['title', 'info_spot__name', 'text_content']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(SpotAccess)
class SpotAccessAdmin(admin.ModelAdmin):
    list_display = ['info_spot', 'user', 'content_language', 'accessed_at', 'audio_played']
    list_filter = ['content_language', 'audio_played', 'text_viewed', 'accessed_at']
    search_fields = ['info_spot__name', 'user__username', 'session_id']
    readonly_fields = ['accessed_at']


@admin.register(UserCredit)
class UserCreditAdmin(admin.ModelAdmin):
    list_display = ['user', 'balance', 'total_purchased', 'total_spent', 'updated_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['updated_at']


@admin.register(CreditPurchase)
class CreditPurchaseAdmin(admin.ModelAdmin):
    list_display = ['user', 'credits_purchased', 'amount', 'status', 'created_at']
    list_filter = ['status', 'currency', 'created_at']
    search_fields = ['user__username', 'stripe_payment_intent_id']
    readonly_fields = ['created_at', 'completed_at']


@admin.register(CreditTransaction)
class CreditTransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'info_spot', 'credits_spent', 'transaction_type', 'created_at']
    list_filter = ['transaction_type', 'created_at', 'tenant']
    search_fields = ['user__username', 'info_spot__name']
    readonly_fields = ['created_at']