from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import InfoSpot, EndUser, UserCredit, Content
from .utils import generate_qr_code_data, generate_nfc_tag_id

User = get_user_model()


@receiver(post_save, sender=InfoSpot)
def generate_info_spot_identifiers(sender, instance, created, **kwargs):
    """Generate QR code and NFC tag ID when InfoSpot is created"""
    if created:
        # Generate QR code data
        if not instance.qr_code_data:
            instance.qr_code_data = generate_qr_code_data(instance)
        
        # Generate NFC tag ID if not provided
        if not instance.nfc_tag_id:
            instance.nfc_tag_id = generate_nfc_tag_id()
        
        # Save without triggering signal again
        InfoSpot.objects.filter(pk=instance.pk).update(
            qr_code_data=instance.qr_code_data,
            nfc_tag_id=instance.nfc_tag_id
        )


@receiver(post_save, sender=User)
def create_end_user_profile(sender, instance, created, **kwargs):
    """Create EndUser profile when User is created"""
    if created:
        EndUser.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def create_user_credit_account(sender, instance, created, **kwargs):
    """Create UserCredit account when User is created"""
    if created:
        UserCredit.objects.get_or_create(user=instance)


@receiver(post_save, sender=Content)
def increment_content_version(sender, instance, created, **kwargs):
    """Increment version number when content is updated"""
    if not created:
        # Only increment version for updates, not creation
        Content.objects.filter(pk=instance.pk).update(
            version=instance.version + 1
        )