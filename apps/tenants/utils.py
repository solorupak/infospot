import secrets
import string
from qr_code.qrcode.utils import QRCodeOptions
# from qr_code.qrcode.maker import make_qr_code_image
from django.conf import settings
from .middleware import get_current_tenant, set_current_tenant, clear_current_tenant


def generate_qr_code_data(info_spot):
    """Generate QR code URL for info spot"""
    # Use HTTPS in production, HTTP in development
    protocol = 'https' if not settings.DEBUG else 'http'
    port = ':8000' if settings.DEBUG else ''
    
    url = f"{protocol}://{info_spot.tenant.subdomain}.{settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost'}{port}/spot/{info_spot.uuid}"
    return url


def generate_qr_code_image(info_spot):
    """Generate QR code image for info spot"""
    url = generate_qr_code_data(info_spot)
    
    # Update the info spot with QR code data
    info_spot.qr_code_data = url
    info_spot.save(update_fields=['qr_code_data'])
    
    # Generate QR code image
    options = QRCodeOptions(size='L', border=4, error_correction='M')
    # qr_image = make_qr_code_image(url, qr_code_options=options)
    # return qr_image


def generate_nfc_tag_id():
    """Generate a unique NFC tag identifier"""
    # Generate a 12-character alphanumeric ID
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(12))


def get_tenant_context(request):
    """Get tenant context for templates"""
    tenant = getattr(request, 'tenant', None)
    if tenant:
        return {
            'tenant': tenant,
            'tenant_name': tenant.name,
            'tenant_subdomain': tenant.subdomain,
            'tenant_logo': tenant.logo.url if tenant.logo else None,
            'tenant_primary_color': tenant.primary_color,
            'tenant_secondary_color': tenant.secondary_color,
        }
    return {}


def is_tenant_admin(user, tenant):
    """Check if user is an admin for the given tenant"""
    if not user.is_authenticated or not tenant:
        return False
    
    from .models import TenantAdmin
    return TenantAdmin.objects.filter(user=user, tenant=tenant).exists()


def get_user_tenant_role(user, tenant):
    """Get user's role for the given tenant"""
    if not user.is_authenticated or not tenant:
        return None
    
    from .models import TenantAdmin
    try:
        tenant_admin = TenantAdmin.objects.get(user=user, tenant=tenant)
        return tenant_admin.role
    except TenantAdmin.DoesNotExist:
        return None