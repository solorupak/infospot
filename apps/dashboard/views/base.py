from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView
from django.http import JsonResponse
from django.urls import reverse
from django.db.models import Q
from apps.tenants.models import Tenant, TenantAdmin
from apps.tenants.utils import get_current_tenant


class DashboardBaseView(LoginRequiredMixin, TemplateView):
    """Base view for all dashboard views"""
    template_name = 'dashboard/base.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Check dashboard permissions
        if not self.has_dashboard_permission(request.user):
            if request.headers.get('HX-Request'):
                return JsonResponse({'error': 'Access denied'}, status=403)
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
    
    def has_dashboard_permission(self, user):
        """Check if user has dashboard access"""
        # Check if user is authenticated first
        if not user.is_authenticated:
            return False
            
        # Platform admins have full access
        if user.is_superuser:
            return True
        
        # Tenant admins have access to their tenant's data
        tenant = get_current_tenant()
        if tenant:
            return TenantAdmin.objects.filter(user=user, tenant=tenant).exists()
        
        # Check if user is a tenant admin for any tenant
        return TenantAdmin.objects.filter(user=user).exists()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'current_tenant': get_current_tenant(),
            'is_platform_admin': self.request.user.is_superuser,
            'dashboard_nav': self.get_navigation_items(),
        })
        return context
    
    def get_navigation_items(self):
        """Get navigation items based on user permissions"""
        nav_items = []
        
        if self.request.user.is_superuser:
            nav_items.extend([
                {'name': 'Tenants', 'url': 'dashboard:tenant_list', 'icon': 'fas fa-building'},
                {'name': 'Tenant Admins', 'url': 'dashboard:tenant_admin_list', 'icon': 'fas fa-users-cog'},
                {'name': 'End Users', 'url': 'dashboard:end_user_list', 'icon': 'fas fa-users'},
                {'name': 'Credits', 'url': 'dashboard:credit_list', 'icon': 'fas fa-coins'},
                {'name': 'Purchases', 'url': 'dashboard:purchase_list', 'icon': 'fas fa-shopping-cart'},
            ])
        
        # Tenant admin items
        nav_items.extend([
            {'name': 'Info Spots', 'url': 'dashboard:info_spot_list', 'icon': 'fas fa-map-marker-alt'},
            {'name': 'Content', 'url': 'dashboard:content_list', 'icon': 'fas fa-file-alt'},
            {'name': 'Analytics', 'url': 'dashboard:analytics', 'icon': 'fas fa-chart-bar'},
            {'name': 'Revenue', 'url': 'dashboard:revenue', 'icon': 'fas fa-dollar-sign'},
        ])
        
        return nav_items


class CRUDBaseView(DashboardBaseView, ListView):
    """Base view for CRUD operations"""
    model = None
    form_class = None
    template_name_suffix = '_list'
    paginate_by = 25
    search_fields = []
    filter_fields = []
    
    def get_queryset(self):
        """Get filtered and searched queryset"""
        queryset = self.model.objects.all()
        
        # Apply tenant filtering for tenant-scoped models
        if hasattr(self.model, 'tenant') and not self.request.user.is_superuser:
            tenant = get_current_tenant()
            if tenant:
                queryset = queryset.filter(tenant=tenant)
        
        # Apply search
        search_query = self.request.GET.get('search')
        if search_query and self.search_fields:
            search_filter = Q()
            for field in self.search_fields:
                search_filter |= Q(**{f"{field}__icontains": search_query})
            queryset = queryset.filter(search_filter)
        
        # Apply filters
        for field in self.filter_fields:
            value = self.request.GET.get(field)
            if value:
                queryset = queryset.filter(**{field: value})
        
        # Apply sorting
        sort_field = self.request.GET.get('sort', '-created_at')
        if sort_field and hasattr(self.model, sort_field.lstrip('-')):
            queryset = queryset.order_by(sort_field)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'model_name': self.model._meta.verbose_name,
            'model_name_plural': self.model._meta.verbose_name_plural,
            'search_query': self.request.GET.get('search', ''),
            'current_filters': {k: v for k, v in self.request.GET.items() 
                              if k in self.filter_fields},
            'sort_field': self.request.GET.get('sort', '-created_at'),
        })
        return context
    
    def render_to_response(self, context, **response_kwargs):
        """Handle HTMX requests with partial templates"""
        if self.request.headers.get('HX-Request'):
            # Return partial template for HTMX requests
            self.template_name = f'dashboard/components/table.html'
        return super().render_to_response(context, **response_kwargs)