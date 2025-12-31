import secrets
import string
from qr_code.qrcode.utils import QRCodeOptions
# from qr_code.qrcode.maker import make_qr_code_image
from django.conf import settings
from django_tenants.utils import get_tenant_model, get_public_schema_name
from django.db import connection


def get_current_tenant():
    """Get the current tenant from django-tenants connection"""
    if hasattr(connection, 'tenant'):
        return connection.tenant
    return None


def get_current_schema_name():
    """Get the current schema name"""
    if hasattr(connection, 'schema_name'):
        return connection.schema_name
    return get_public_schema_name()


def is_public_schema():
    """Check if we're currently in the public schema"""
    return get_current_schema_name() == get_public_schema_name()


def generate_qr_code_data(info_spot):
    """Generate QR code URL for info spot"""
    # Get current tenant from django-tenants connection
    tenant = get_current_tenant()
    if not tenant:
        raise ValueError("Cannot generate QR code data without tenant context")
    
    # Use HTTPS in production, HTTP in development
    protocol = 'https' if not settings.DEBUG else 'http'
    port = ':8000' if settings.DEBUG else ''
    
    # Get the primary domain for this tenant
    primary_domain = tenant.domains.filter(is_primary=True).first()
    if not primary_domain:
        raise ValueError(f"No primary domain found for tenant {tenant.name}")
    
    url = f"{protocol}://{primary_domain.domain}{port}/spot/{info_spot.uuid}"
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
        # Get primary domain for subdomain display
        primary_domain = tenant.domains.filter(is_primary=True).first()
        subdomain = primary_domain.domain.split('.')[0] if primary_domain else 'unknown'
        
        return {
            'tenant': tenant,
            'tenant_name': tenant.name,
            'tenant_subdomain': subdomain,
            'tenant_logo': tenant.logo.url if tenant.logo else None,
            'tenant_primary_color': tenant.primary_color,
            'tenant_secondary_color': tenant.secondary_color,
        }
    return {}


def is_tenant_admin(user, tenant=None):
    """Check if user is an admin for the given tenant"""
    if not user.is_authenticated:
        return False
    
    # If no tenant provided, use current tenant
    if not tenant:
        tenant = get_current_tenant()
    
    if not tenant:
        return False
    
    from .models import TenantAdmin
    return TenantAdmin.objects.filter(user=user, tenant=tenant).exists()


def get_user_tenant_role(user, tenant=None):
    """Get user's role for the given tenant"""
    if not user.is_authenticated:
        return None
    
    # If no tenant provided, use current tenant
    if not tenant:
        tenant = get_current_tenant()
    
    if not tenant:
        return None
    
    from .models import TenantAdmin
    try:
        tenant_admin = TenantAdmin.objects.get(user=user, tenant=tenant)
        return tenant_admin.role
    except TenantAdmin.DoesNotExist:
        return None