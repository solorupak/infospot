from .utils import get_tenant_context, is_tenant_admin, get_user_tenant_role


def tenant_context(request):
    """Add tenant context to all templates"""
    context = get_tenant_context(request)
    
    # Add tenant admin status if user is authenticated
    if hasattr(request, 'user') and request.user.is_authenticated and hasattr(request, 'tenant'):
        context.update({
            'is_tenant_admin': is_tenant_admin(request.user, request.tenant),
            'tenant_role': get_user_tenant_role(request.user, request.tenant),
        })
    
    return context