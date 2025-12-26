import threading
from django.http import HttpResponseNotFound
from django.shortcuts import get_object_or_404
from .models import Tenant

# Thread-local storage for tenant context
_thread_locals = threading.local()


def get_current_tenant():
    """Get the current tenant from thread-local storage"""
    return getattr(_thread_locals, 'tenant', 1)


def set_current_tenant(tenant):
    """Set the current tenant in thread-local storage"""
    _thread_locals.tenant = tenant


def clear_current_tenant():
    """Clear the current tenant from thread-local storage"""
    if hasattr(_thread_locals, 'tenant'):
        delattr(_thread_locals, 'tenant')


class TenantMiddleware:
    """
    Extracts tenant from subdomain and sets active tenant context.
    Handles both tenant admin and end user requests.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Extract subdomain from request.get_host()
        host = request.get_host().split(':')[0]
        subdomain = self.extract_subdomain(host)
        
        if subdomain and subdomain != 'www':
            try:
                tenant = Tenant.objects.get(subdomain=subdomain, is_active=True)
                request.tenant = tenant
                # Set thread-local for query filtering
                set_current_tenant(tenant)
            except Tenant.DoesNotExist:
                return HttpResponseNotFound("Tenant not found")
        else:
            request.tenant = None
            clear_current_tenant()
        
        response = self.get_response(request)
        
        # Clear tenant context after request
        clear_current_tenant()
        return response
    
    def extract_subdomain(self, host):
        """Extract subdomain from host"""
        # Remove port if present
        host = host.split(':')[0]
        
        # Split by dots and check if we have a subdomain
        parts = host.split('.')
        
        # For development (localhost), no subdomain
        if host in ['localhost', '127.0.0.1']:
            return None
            
        # For production domains like museum.infospot.com
        if len(parts) >= 3:
            return parts[0]
        
        # For development with custom hosts like museum.localhost
        if len(parts) == 2 and parts[1] in ['localhost', 'local']:
            return parts[0]
            
        return None


class TenantQuerySetMixin:
    """
    Automatically filters querysets by current tenant.
    Applied to all tenant-scoped models.
    """
    
    def get_queryset(self):
        qs = super().get_queryset()
        tenant = get_current_tenant()
        if tenant and hasattr(self.model, 'tenant'):
            return qs.filter(tenant=tenant)
        return qs