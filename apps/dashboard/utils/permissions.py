from functools import wraps
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from apps.tenants.models import TenantAdmin
from apps.tenants.utils import get_current_tenant


def has_dashboard_permission(user):
    """Check if user has dashboard access"""
    # Check if user is authenticated first
    if not user.is_authenticated:
        return False
        
    if user.is_superuser:
        return True
    
    # Check if user is a tenant admin
    return TenantAdmin.objects.filter(user=user).exists()


def has_tenant_permission(user, tenant=None):
    """Check if user has permission for specific tenant"""
    # Check if user is authenticated first
    if not user.is_authenticated:
        return False
        
    if user.is_superuser:
        return True
    
    if tenant is None:
        tenant = get_current_tenant()
    
    if tenant:
        return TenantAdmin.objects.filter(user=user, tenant=tenant).exists()
    
    return False


def require_platform_admin(view_func):
    """Decorator to require platform admin access"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_superuser:
            if request.headers.get('HX-Request'):
                return JsonResponse({'error': 'Platform admin access required'}, status=403)
            raise PermissionDenied("Platform admin access required")
        return view_func(request, *args, **kwargs)
    return wrapper


def require_tenant_admin(view_func):
    """Decorator to require tenant admin access"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not has_tenant_permission(request.user):
            if request.headers.get('HX-Request'):
                return JsonResponse({'error': 'Tenant admin access required'}, status=403)
            raise PermissionDenied("Tenant admin access required")
        return view_func(request, *args, **kwargs)
    return wrapper


def get_user_tenants(user):
    """Get all tenants that user has admin access to"""
    if not user.is_authenticated:
        from apps.tenants.models import Tenant
        return Tenant.objects.none()
        
    if user.is_superuser:
        from apps.tenants.models import Tenant
        return Tenant.objects.filter(is_active=True)
    
    tenant_admins = TenantAdmin.objects.filter(user=user).select_related('tenant')
    return [ta.tenant for ta in tenant_admins if ta.tenant.is_active]


def get_user_role_for_tenant(user, tenant):
    """Get user's role for a specific tenant"""
    if not user.is_authenticated:
        return None
        
    if user.is_superuser:
        return 'platform_admin'
    
    try:
        tenant_admin = TenantAdmin.objects.get(user=user, tenant=tenant)
        return tenant_admin.role
    except TenantAdmin.DoesNotExist:
        return None