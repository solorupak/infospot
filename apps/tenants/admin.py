from django.contrib import admin
from .models import Tenant, Domain, TenantAdmin, EndUser, UserCredit, CreditPurchase


class DomainInline(admin.TabularInline):
    model = Domain
    extra = 1


@admin.register(Tenant)
class TenantModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'schema_name', 'venue_type', 'is_active', 'on_trial', 'paid_until', 'created_at']
    list_filter = ['venue_type', 'is_active', 'on_trial', 'created_at']
    search_fields = ['name', 'schema_name', 'contact_email']
    readonly_fields = ['schema_name', 'created_at', 'updated_at']
    inlines = [DomainInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'schema_name', 'venue_type', 'contact_email', 'timezone', 'is_active')
        }),
        ('Subscription', {
            'fields': ('on_trial', 'paid_until')
        }),
        ('Branding', {
            'fields': ('logo', 'primary_color', 'secondary_color')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ['domain', 'tenant', 'is_primary']
    list_filter = ['is_primary']
    search_fields = ['domain', 'tenant__name']


@admin.register(TenantAdmin)
class TenantAdminModelAdmin(admin.ModelAdmin):
    list_display = ['user', 'tenant', 'role', 'created_at']
    list_filter = ['role', 'created_at', 'tenant']
    search_fields = ['user__username', 'user__email', 'tenant__name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(EndUser)
class EndUserAdmin(admin.ModelAdmin):
    list_display = ['user', 'preferred_language', 'phone_number', 'created_at']
    list_filter = ['preferred_language', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone_number']
    readonly_fields = ['created_at', 'updated_at']


# Public schema models (credit management - shared across tenants)
@admin.register(UserCredit)
class UserCreditAdmin(admin.ModelAdmin):
    list_display = ['user', 'balance', 'total_purchased', 'total_spent', 'updated_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['total_purchased', 'total_spent', 'created_at', 'updated_at']
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Credit Balance', {
            'fields': ('balance',)
        }),
        ('Statistics', {
            'fields': ('total_purchased', 'total_spent'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CreditPurchase)
class CreditPurchaseAdmin(admin.ModelAdmin):
    list_display = ['user', 'credits_purchased', 'amount', 'currency', 'status', 'created_at']
    list_filter = ['status', 'currency', 'created_at']
    search_fields = ['user__username', 'user__email', 'stripe_payment_intent_id']
    readonly_fields = ['stripe_payment_intent_id', 'created_at', 'updated_at', 'completed_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Purchase Information', {
            'fields': ('user', 'credits_purchased', 'amount', 'currency', 'price_per_credit')
        }),
        ('Payment Details', {
            'fields': ('stripe_payment_intent_id', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )