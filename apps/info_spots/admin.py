from django.contrib import admin
from .models import InfoSpot, Content, SpotAccess, CreditTransaction


class ContentInline(admin.TabularInline):
    model = Content
    extra = 1
    fields = ['language', 'title', 'text_content', 'audio_file', 'version']


@admin.register(InfoSpot)
class InfoSpotAdmin(admin.ModelAdmin):
    list_display = ['name', 'access_type', 'credit_cost', 'is_active', 'created_at']
    list_filter = ['access_type', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'location_description']
    readonly_fields = ['uuid', 'qr_code_data', 'created_at', 'updated_at']
    inlines = [ContentInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'location_description')
        }),
        ('Access Control', {
            'fields': ('access_type', 'credit_cost')
        }),
        ('Identifiers', {
            'fields': ('uuid', 'qr_code_data', 'nfc_tag_id')
        }),
        ('Status & Ordering', {
            'fields': ('is_active', 'display_order')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Auto-generate QR code data when saving"""
        if not obj.qr_code_data:
            # This will be implemented when we have tenant context
            obj.qr_code_data = f"https://example.com/spot/{obj.uuid}"
        super().save_model(request, obj, form, change)


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = ['title', 'info_spot', 'language', 'version', 'has_audio', 'created_at']
    list_filter = ['language', 'version', 'created_at']
    search_fields = ['title', 'info_spot__name', 'text_content']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('info_spot', 'language', 'title')
        }),
        ('Content', {
            'fields': ('text_content', 'audio_file', 'audio_duration')
        }),
        ('Versioning', {
            'fields': ('version',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_audio(self, obj):
        """Display whether content has audio file"""
        return bool(obj.audio_file)
    has_audio.boolean = True
    has_audio.short_description = 'Has Audio'


@admin.register(SpotAccess)
class SpotAccessAdmin(admin.ModelAdmin):
    list_display = ['info_spot', 'user_display', 'content_language', 'created_at', 'audio_played', 'text_viewed']
    list_filter = ['content_language', 'audio_played', 'text_viewed', 'created_at']
    search_fields = ['info_spot__name', 'user__username', 'session_id', 'ip_address']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    def user_display(self, obj):
        """Display user or 'Anonymous' for null users"""
        return obj.user.username if obj.user else 'Anonymous'
    user_display.short_description = 'User'
    
    fieldsets = (
        ('Access Information', {
            'fields': ('info_spot', 'user', 'content_language')
        }),
        ('Session Details', {
            'fields': ('session_id', 'ip_address', 'user_agent')
        }),
        ('Content Consumption', {
            'fields': ('audio_played', 'audio_play_duration', 'text_viewed')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CreditTransaction)
class CreditTransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'info_spot', 'credits_spent', 'transaction_type', 'created_at']
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['user__username', 'user__email', 'info_spot__name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Transaction Information', {
            'fields': ('user', 'info_spot', 'credits_spent', 'transaction_type')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )