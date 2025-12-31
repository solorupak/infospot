import uuid
from django.core.validators import FileExtensionValidator
from django.db import models
from django.conf import settings


class InfoSpot(models.Model):
    """Represents a physical location with QR/NFC code"""
    # No tenant foreign key needed - django-tenants handles schema isolation
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    
    # Basic Information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    location_description = models.CharField(max_length=500, blank=True)
    
    # Access Control
    access_type = models.CharField(
        max_length=20,
        choices=[
            ('free_ticketed', 'Free (Ticketed Venue)'),
            ('free_public', 'Free (Public)'),
            ('paid', 'Paid (Credits Required)')
        ]
    )
    credit_cost = models.IntegerField(
        default=1,
        help_text="Number of credits required to access this spot"
    )
    
    # QR/NFC Identifiers
    qr_code_data = models.CharField(max_length=500, unique=True)
    nfc_tag_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Ordering
    display_order = models.IntegerField(default=0)
    
    # Add timestamps manually
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['uuid']),
            models.Index(fields=['qr_code_data']),
            models.Index(fields=['nfc_tag_id']),
        ]
        ordering = ['display_order', 'name']


class Content(models.Model):
    """Audio and text content for info spots"""
    info_spot = models.ForeignKey(InfoSpot, on_delete=models.CASCADE, related_name='contents')
    language = models.CharField(max_length=10, default='en')
    
    # Content Types
    title = models.CharField(max_length=255)
    text_content = models.TextField(blank=True)
    audio_file = models.FileField(
        upload_to='audio_content/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(['mp3', 'wav', 'aac', 'm4a'])]
    )
    audio_duration = models.IntegerField(
        null=True,
        blank=True,
        help_text="Duration in seconds"
    )
    
    # Metadata
    version = models.IntegerField(default=1)
    
    # Add timestamps manually
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('info_spot', 'language')

    def __str__(self):
        return f"{self.title} ({self.language}) - {self.info_spot.name}"


class SpotAccess(models.Model):
    """Tracks user access to info spots"""
    info_spot = models.ForeignKey(InfoSpot, on_delete=models.CASCADE)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Null for anonymous ticketed venue access"
    )
    
    # Access Details
    session_id = models.CharField(max_length=100, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    
    # Content Consumption
    content_language = models.CharField(max_length=10)
    audio_played = models.BooleanField(default=False)
    audio_play_duration = models.IntegerField(
        null=True,
        blank=True,
        help_text="Seconds of audio played"
    )
    text_viewed = models.BooleanField(default=False)
    
    # Add timestamps manually
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['info_spot', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['session_id']),
        ]

    def __str__(self):
        user_str = self.user.username if self.user else "Anonymous"
        return f"{user_str} accessed {self.info_spot.name} at {self.created_at}"


class CreditTransaction(models.Model):
    """Tracks individual credit spending on spots"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    info_spot = models.ForeignKey(InfoSpot, on_delete=models.CASCADE)
    # No tenant foreign key needed - django-tenants handles schema isolation
    
    # Transaction Details
    credits_spent = models.IntegerField()
    transaction_type = models.CharField(
        max_length=20,
        choices=[
            ('spot_access', 'Spot Access'),
            ('refund', 'Refund')
        ],
        default='spot_access'
    )
    
    # Add timestamps manually
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['info_spot', 'user']),  # Check if already accessed
        ]

    def __str__(self):
        return f"{self.user.username} spent {self.credits_spent} credits on {self.info_spot.name}"