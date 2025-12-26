import uuid
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
from django.db import models

User = get_user_model()


class Tenant(models.Model):
    """Represents an organization using the platform"""
    subdomain = models.SlugField(unique=True, max_length=63)
    name = models.CharField(max_length=255)
    venue_type = models.CharField(
        max_length=50,
        choices=[
            ('ticketed', 'Ticketed Venue'),
            ('public', 'Public Spots'),
            ('mixed', 'Mixed')
        ]
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Branding
    logo = models.ImageField(upload_to='tenant_logos/', null=True, blank=True)
    primary_color = models.CharField(max_length=7, default='#007bff')
    secondary_color = models.CharField(max_length=7, default='#6c757d')
    
    # Metadata
    contact_email = models.EmailField()
    timezone = models.CharField(max_length=50, default='UTC')

    def __str__(self):
        return f"{self.name} ({self.subdomain})"

    class Meta:
        ordering = ['name']


class TenantAdmin(models.Model):
    """Admin users for specific tenants"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    role = models.CharField(
        max_length=50,
        choices=[
            ('owner', 'Owner'),
            ('admin', 'Administrator'),
            ('editor', 'Content Editor')
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'tenant')

    def __str__(self):
        return f"{self.user.username} - {self.tenant.name} ({self.role})"


class EndUser(models.Model):
    """Global end user accounts (extends Django User)"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    preferred_language = models.CharField(max_length=10, default='en')
    phone_number = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"EndUser: {self.user.username}"


class InfoSpot(models.Model):
    """Represents a physical location with QR/NFC code"""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Ordering
    display_order = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.name} ({self.tenant.name})"

    class Meta:
        indexes = [
            models.Index(fields=['tenant', 'is_active']),
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
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Null for anonymous ticketed venue access"
    )
    
    # Access Details
    accessed_at = models.DateTimeField(auto_now_add=True)
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

    class Meta:
        indexes = [
            models.Index(fields=['info_spot', 'accessed_at']),
            models.Index(fields=['user', 'accessed_at']),
            models.Index(fields=['session_id']),
        ]

    def __str__(self):
        user_str = self.user.username if self.user else "Anonymous"
        return f"{user_str} accessed {self.info_spot.name} at {self.accessed_at}"


class UserCredit(models.Model):
    """Tracks user credit balance"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='credits')
    balance = models.IntegerField(default=0, help_text="Number of credits available")
    total_purchased = models.IntegerField(default=0, help_text="Total credits ever purchased")
    total_spent = models.IntegerField(default=0, help_text="Total credits ever spent")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}: {self.balance} credits"


class CreditPurchase(models.Model):
    """Tracks credit purchase transactions"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Purchase Details
    credits_purchased = models.IntegerField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    price_per_credit = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Payment Details
    stripe_payment_intent_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('succeeded', 'Succeeded'),
            ('failed', 'Failed'),
            ('refunded', 'Refunded')
        ]
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['stripe_payment_intent_id']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.credits_purchased} credits ({self.status})"


class CreditTransaction(models.Model):
    """Tracks individual credit spending on spots"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    info_spot = models.ForeignKey(InfoSpot, on_delete=models.CASCADE)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    
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
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['tenant', 'created_at']),
            models.Index(fields=['info_spot', 'user']),  # Check if already accessed
        ]

    def __str__(self):
        return f"{self.user.username} spent {self.credits_spent} credits on {self.info_spot.name}"