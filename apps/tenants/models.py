import uuid
from django.core.validators import FileExtensionValidator
from django.db import models
from django.conf import settings
from django_tenants.models import TenantMixin, DomainMixin


class Tenant(TenantMixin):
    """Represents an organization using the platform"""
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
    
    # Subscription fields
    paid_until = models.DateField()
    on_trial = models.BooleanField(default=True)
    
    # Branding
    logo = models.ImageField(upload_to='tenant_logos/', null=True, blank=True)
    primary_color = models.CharField(max_length=7, default='#007bff')
    secondary_color = models.CharField(max_length=7, default='#6c757d')
    
    # Metadata
    contact_email = models.EmailField()
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Add timestamps manually since we removed BaseModel
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Required by django-tenants
    auto_create_schema = True
    auto_drop_schema = False

    def __str__(self):
        return f"{self.name} ({self.schema_name})"

    class Meta:
        ordering = ['name']


class Domain(DomainMixin):
    """Domain model for mapping subdomains to tenants"""
    pass


class TenantAdmin(models.Model):
    """Admin users for specific tenants"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    role = models.CharField(
        max_length=50,
        choices=[
            ('owner', 'Owner'),
            ('admin', 'Administrator'),
            ('editor', 'Content Editor')
        ]
    )
    
    # Add timestamps manually
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'tenant')

    def __str__(self):
        return f"{self.user.username} - {self.tenant.name} ({self.role})"


class EndUser(models.Model):
    """Global end user accounts (extends Django User)"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    preferred_language = models.CharField(max_length=10, default='en')
    phone_number = models.CharField(max_length=20, blank=True)
    
    # Add timestamps manually
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"EndUser: {self.user.username}"

# The models below have been moved to apps.info_spots since they are tenant-specific
# and should be in the tenant schema, not the public schema


class UserCredit(models.Model):
    """Tracks user credit balance - Public schema model"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='credits')
    balance = models.IntegerField(default=0, help_text="Number of credits available")
    total_purchased = models.IntegerField(default=0, help_text="Total credits ever purchased")
    total_spent = models.IntegerField(default=0, help_text="Total credits ever spent")
    
    # Add timestamps manually
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}: {self.balance} credits"


class CreditPurchase(models.Model):
    """Tracks credit purchase transactions - Public schema model"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
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
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['stripe_payment_intent_id']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.credits_purchased} credits ({self.status})"