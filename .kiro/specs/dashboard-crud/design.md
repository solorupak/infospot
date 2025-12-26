# Design Document: Dashboard CRUD System

## Overview

This document outlines the technical design for a comprehensive dashboard application that provides CRUD operations for all models in the multi-tenant info spots platform. The dashboard will be built as a separate Django app using a component-based architecture with HTMX for dynamic interactions and Bootstrap for responsive UI.

**Technology Stack:**
- Backend: Django 5.x with existing multi-tenant infrastructure
- Frontend: HTMX 1.9+, Bootstrap 5.3+, Alpine.js for complex interactions
- Database: PostgreSQL (using existing models)
- Real-time: Django Channels with WebSockets for live updates
- Charts: Chart.js for analytics visualization
- Export: django-import-export for CSV/Excel operations

## Architecture

### App Structure

The dashboard will be organized as a Django app with the following structure:

```
apps/dashboard/
├── __init__.py
├── apps.py
├── urls.py
├── views/
│   ├── __init__.py
│   ├── base.py              # Base view classes
│   ├── tenant.py            # Tenant CRUD views
│   ├── tenant_admin.py      # TenantAdmin CRUD views
│   ├── end_user.py          # EndUser CRUD views
│   ├── info_spot.py         # InfoSpot CRUD views
│   ├── content.py           # Content CRUD views
│   ├── analytics.py         # Analytics views
│   ├── credits.py           # Credit management views
│   └── api.py               # HTMX API endpoints
├── forms/
│   ├── __init__.py
│   ├── base.py              # Base form classes
│   ├── tenant.py            # Tenant forms
│   ├── tenant_admin.py      # TenantAdmin forms
│   ├── end_user.py          # EndUser forms
│   ├── info_spot.py         # InfoSpot forms
│   ├── content.py           # Content forms
│   └── bulk.py              # Bulk operation forms
├── templates/dashboard/
│   ├── base.html            # Base dashboard template
│   ├── components/          # Reusable components
│   │   ├── table.html       # Data table component
│   │   ├── form.html        # Form component
│   │   ├── modal.html       # Modal component
│   │   ├── pagination.html  # Pagination component
│   │   ├── search.html      # Search component
│   │   └── charts.html      # Chart components
│   ├── tenant/              # Tenant CRUD templates
│   ├── tenant_admin/        # TenantAdmin CRUD templates
│   ├── end_user/           # EndUser CRUD templates
│   ├── info_spot/          # InfoSpot CRUD templates
│   ├── content/            # Content CRUD templates
│   ├── analytics/          # Analytics templates
│   └── credits/            # Credit management templates
├── static/dashboard/
│   ├── css/
│   │   └── dashboard.css    # Custom dashboard styles
│   ├── js/
│   │   ├── dashboard.js     # Main dashboard JavaScript
│   │   ├── components.js    # Component behaviors
│   │   └── charts.js        # Chart configurations
│   └── img/
├── templatetags/
│   ├── __init__.py
│   └── dashboard_tags.py    # Custom template tags
├── utils/
│   ├── __init__.py
│   ├── permissions.py       # Permission utilities
│   ├── filters.py           # Search and filter utilities
│   ├── export.py            # Export utilities
│   └── pagination.py       # Pagination utilities
├── management/
│   └── commands/
│       └── create_sample_data.py  # Sample data for testing
└── tests/
    ├── __init__.py
    ├── test_views.py
    ├── test_forms.py
    ├── test_permissions.py
    └── test_components.py
```

### Component-Based Architecture

The dashboard uses a component-based approach where UI elements are modular and reusable:

#### Base Components

**Table Component** (`components/table.html`):
```html
<!-- Reusable data table with sorting, filtering, and pagination -->
<div class="table-container" 
     hx-get="{% url table_url %}" 
     hx-trigger="load, search-updated from:body"
     hx-target="this"
     hx-swap="outerHTML">
    
    <div class="table-header">
        <div class="row">
            <div class="col-md-6">
                {% include 'dashboard/components/search.html' %}
            </div>
            <div class="col-md-6 text-end">
                {% include 'dashboard/components/bulk_actions.html' %}
            </div>
        </div>
    </div>
    
    <div class="table-responsive">
        <table class="table table-striped table-hover">
            <thead>
                {% for column in columns %}
                <th>
                    {% if column.sortable %}
                    <a href="#" 
                       hx-get="{% url table_url %}?sort={{ column.field }}"
                       hx-target=".table-container"
                       hx-swap="outerHTML">
                        {{ column.label }}
                        <i class="fas fa-sort"></i>
                    </a>
                    {% else %}
                    {{ column.label }}
                    {% endif %}
                </th>
                {% endfor %}
                <th>Actions</th>
            </thead>
            <tbody>
                {% for item in items %}
                <tr>
                    <td>
                        <input type="checkbox" 
                               name="selected_items" 
                               value="{{ item.pk }}"
                               class="bulk-select">
                    </td>
                    {% for column in columns %}
                    <td>{{ item|get_field:column.field }}</td>
                    {% endfor %}
                    <td>
                        {% include 'dashboard/components/row_actions.html' %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    
    {% include 'dashboard/components/pagination.html' %}
</div>
```

**Form Component** (`components/form.html`):
```html
<!-- Reusable form with HTMX submission -->
<form hx-post="{% url form_url %}"
      hx-target="#form-container"
      hx-swap="outerHTML"
      hx-indicator="#form-loading">
    
    {% csrf_token %}
    
    <div id="form-loading" class="htmx-indicator">
        <div class="spinner-border" role="status"></div>
    </div>
    
    {% for field in form %}
    <div class="mb-3">
        <label for="{{ field.id_for_label }}" class="form-label">
            {{ field.label }}
            {% if field.field.required %}
            <span class="text-danger">*</span>
            {% endif %}
        </label>
        
        {% if field.field.widget.input_type == 'file' %}
        <div class="file-upload-wrapper">
            {{ field }}
            <div class="file-preview" id="preview-{{ field.name }}"></div>
        </div>
        {% elif field.field.widget.input_type == 'textarea' %}
        <div class="rich-text-editor">
            {{ field }}
        </div>
        {% else %}
        {{ field }}
        {% endif %}
        
        {% if field.errors %}
        <div class="invalid-feedback d-block">
            {{ field.errors.0 }}
        </div>
        {% endif %}
        
        {% if field.help_text %}
        <div class="form-text">{{ field.help_text }}</div>
        {% endif %}
    </div>
    {% endfor %}
    
    <div class="form-actions">
        <button type="submit" class="btn btn-primary">
            <i class="fas fa-save"></i> Save
        </button>
        <button type="button" class="btn btn-secondary" 
                hx-get="{% url cancel_url %}"
                hx-target="#main-content">
            Cancel
        </button>
    </div>
</form>
```

**Modal Component** (`components/modal.html`):
```html
<!-- Reusable modal for create/edit operations -->
<div class="modal fade" id="{{ modal_id }}" tabindex="-1">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">{{ modal_title }}</h5>
                <button type="button" class="btn-close" 
                        data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body" id="modal-body-{{ modal_id }}">
                {% block modal_content %}{% endblock %}
            </div>
        </div>
    </div>
</div>
```

## Components and Interfaces

### Base View Classes

#### DashboardBaseView
```python
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import JsonResponse
from apps.tenants.utils import get_current_tenant

class DashboardBaseView(LoginRequiredMixin, TemplateView):
    """Base view for all dashboard views"""
    template_name = 'dashboard/base.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Check dashboard permissions
        if not self.has_dashboard_permission(request.user):
            return JsonResponse({'error': 'Access denied'}, status=403)
        return super().dispatch(request, *args, **kwargs)
    
    def has_dashboard_permission(self, user):
        """Check if user has dashboard access"""
        # Platform admins have full access
        if user.is_superuser:
            return True
        
        # Tenant admins have access to their tenant's data
        tenant = get_current_tenant()
        if tenant:
            return hasattr(user, 'tenantadmin_set') and \
                   user.tenantadmin_set.filter(tenant=tenant).exists()
        
        return False
    
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

class CRUDBaseView(DashboardBaseView):
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
            from django.db.models import Q
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
        if sort_field:
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
        })
        return context
```

### Model-Specific Views

#### TenantCRUDViews
```python
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from apps.tenants.models import Tenant
from .forms.tenant import TenantForm, TenantBulkForm

class TenantListView(CRUDBaseView, ListView):
    model = Tenant
    template_name = 'dashboard/tenant/list.html'
    search_fields = ['name', 'subdomain', 'contact_email']
    filter_fields = ['venue_type', 'is_active']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add statistics
        tenants = self.get_queryset()
        context.update({
            'total_tenants': tenants.count(),
            'active_tenants': tenants.filter(is_active=True).count(),
            'venue_types': tenants.values('venue_type').distinct(),
            'columns': [
                {'field': 'name', 'label': 'Name', 'sortable': True},
                {'field': 'subdomain', 'label': 'Subdomain', 'sortable': True},
                {'field': 'venue_type', 'label': 'Type', 'sortable': True},
                {'field': 'is_active', 'label': 'Status', 'sortable': True},
                {'field': 'created_at', 'label': 'Created', 'sortable': True},
            ]
        })
        return context

class TenantCreateView(CRUDBaseView, CreateView):
    model = Tenant
    form_class = TenantForm
    template_name = 'dashboard/tenant/form.html'
    
    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.headers.get('HX-Request'):
            return JsonResponse({
                'success': True,
                'message': f'Tenant "{self.object.name}" created successfully',
                'redirect': reverse('dashboard:tenant_list')
            })
        return response

class TenantUpdateView(CRUDBaseView, UpdateView):
    model = Tenant
    form_class = TenantForm
    template_name = 'dashboard/tenant/form.html'
    
    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.headers.get('HX-Request'):
            return JsonResponse({
                'success': True,
                'message': f'Tenant "{self.object.name}" updated successfully',
                'redirect': reverse('dashboard:tenant_list')
            })
        return response

class TenantDeleteView(CRUDBaseView, DeleteView):
    model = Tenant
    template_name = 'dashboard/tenant/confirm_delete.html'
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        # Soft delete - deactivate instead of actual deletion
        self.object.is_active = False
        self.object.save()
        
        if request.headers.get('HX-Request'):
            return JsonResponse({
                'success': True,
                'message': f'Tenant "{self.object.name}" deactivated successfully'
            })
        return redirect('dashboard:tenant_list')
```

#### InfoSpotCRUDViews
```python
from apps.tenants.models import InfoSpot
from .forms.info_spot import InfoSpotForm

class InfoSpotListView(CRUDBaseView, ListView):
    model = InfoSpot
    template_name = 'dashboard/info_spot/list.html'
    search_fields = ['name', 'description', 'location_description']
    filter_fields = ['access_type', 'is_active']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add analytics data
        spots = self.get_queryset()
        context.update({
            'total_spots': spots.count(),
            'active_spots': spots.filter(is_active=True).count(),
            'paid_spots': spots.filter(access_type='paid').count(),
            'columns': [
                {'field': 'name', 'label': 'Name', 'sortable': True},
                {'field': 'access_type', 'label': 'Access Type', 'sortable': True},
                {'field': 'credit_cost', 'label': 'Credits', 'sortable': True},
                {'field': 'is_active', 'label': 'Status', 'sortable': True},
                {'field': 'created_at', 'label': 'Created', 'sortable': True},
            ]
        })
        return context

class InfoSpotCreateView(CRUDBaseView, CreateView):
    model = InfoSpot
    form_class = InfoSpotForm
    template_name = 'dashboard/info_spot/form.html'
    
    def form_valid(self, form):
        # Set tenant for the info spot
        form.instance.tenant = get_current_tenant()
        
        # Generate QR code data
        form.instance.qr_code_data = self.generate_qr_code_data(form.instance)
        
        response = super().form_valid(form)
        
        if self.request.headers.get('HX-Request'):
            return JsonResponse({
                'success': True,
                'message': f'Info spot "{self.object.name}" created successfully',
                'qr_code_url': reverse('dashboard:info_spot_qr', args=[self.object.pk])
            })
        return response
    
    def generate_qr_code_data(self, info_spot):
        """Generate QR code data URL"""
        tenant = get_current_tenant()
        return f"https://{tenant.subdomain}.infospot.com/spot/{info_spot.uuid}"
```

### Form Classes

#### Base Form Classes
```python
from django import forms
from django.core.exceptions import ValidationError

class DashboardBaseForm(forms.ModelForm):
    """Base form for dashboard forms"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add Bootstrap classes to all fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select'})
            elif isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({'class': 'form-control'})
            else:
                field.widget.attrs.update({'class': 'form-control'})
            
            # Add HTMX attributes for dynamic validation
            if hasattr(field, 'required') and field.required:
                field.widget.attrs.update({
                    'hx-post': reverse('dashboard:validate_field'),
                    'hx-trigger': 'blur',
                    'hx-target': f'#error-{field_name}',
                    'hx-swap': 'innerHTML'
                })

class TenantForm(DashboardBaseForm):
    class Meta:
        model = Tenant
        fields = ['name', 'subdomain', 'venue_type', 'contact_email', 
                 'logo', 'primary_color', 'secondary_color', 'timezone']
        widgets = {
            'primary_color': forms.TextInput(attrs={'type': 'color'}),
            'secondary_color': forms.TextInput(attrs={'type': 'color'}),
            'venue_type': forms.Select(attrs={'hx-get': reverse_lazy('dashboard:venue_type_help')}),
        }
    
    def clean_subdomain(self):
        subdomain = self.cleaned_data['subdomain']
        
        # Validate subdomain format
        import re
        if not re.match(r'^[a-z0-9-]+$', subdomain):
            raise ValidationError('Subdomain can only contain lowercase letters, numbers, and hyphens')
        
        # Check uniqueness (excluding current instance)
        queryset = Tenant.objects.filter(subdomain=subdomain)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise ValidationError('This subdomain is already taken')
        
        return subdomain

class InfoSpotForm(DashboardBaseForm):
    class Meta:
        model = InfoSpot
        fields = ['name', 'description', 'location_description', 
                 'access_type', 'credit_cost', 'display_order']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'access_type': forms.Select(attrs={
                'hx-get': reverse_lazy('dashboard:access_type_help'),
                'hx-target': '#access-type-help'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        access_type = cleaned_data.get('access_type')
        credit_cost = cleaned_data.get('credit_cost')
        
        if access_type == 'paid' and (not credit_cost or credit_cost <= 0):
            raise ValidationError('Paid spots must have a credit cost greater than 0')
        
        if access_type != 'paid' and credit_cost and credit_cost > 0:
            cleaned_data['credit_cost'] = 0
        
        return cleaned_data
```

### Analytics and Reporting

#### Analytics Views
```python
from django.db.models import Count, Sum, Avg
from django.utils import timezone
from datetime import timedelta

class AnalyticsView(DashboardBaseView):
    template_name = 'dashboard/analytics/overview.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Date range filtering
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        if not date_from:
            date_from = timezone.now() - timedelta(days=30)
        if not date_to:
            date_to = timezone.now()
        
        # Get analytics data
        tenant = get_current_tenant()
        spots = InfoSpot.objects.filter(tenant=tenant) if tenant else InfoSpot.objects.all()
        
        # Access analytics
        access_data = SpotAccess.objects.filter(
            info_spot__in=spots,
            accessed_at__range=[date_from, date_to]
        )
        
        # Revenue analytics
        revenue_data = CreditTransaction.objects.filter(
            tenant=tenant if tenant else None,
            created_at__range=[date_from, date_to]
        )
        
        context.update({
            'total_spots': spots.count(),
            'total_accesses': access_data.count(),
            'unique_users': access_data.values('user').distinct().count(),
            'total_revenue': revenue_data.aggregate(Sum('credits_spent'))['credits_spent__sum'] or 0,
            'popular_spots': access_data.values('info_spot__name').annotate(
                access_count=Count('id')
            ).order_by('-access_count')[:10],
            'daily_accesses': self.get_daily_access_data(access_data),
            'revenue_by_spot': self.get_revenue_by_spot(revenue_data),
        })
        
        return context
    
    def get_daily_access_data(self, access_data):
        """Get daily access counts for charts"""
        return access_data.extra(
            select={'day': 'date(accessed_at)'}
        ).values('day').annotate(
            count=Count('id')
        ).order_by('day')
    
    def get_revenue_by_spot(self, revenue_data):
        """Get revenue breakdown by spot"""
        return revenue_data.values('info_spot__name').annotate(
            total_revenue=Sum('credits_spent')
        ).order_by('-total_revenue')
```

### Real-time Updates

#### WebSocket Consumer
```python
from channels.generic.websocket import AsyncWebsocketConsumer
import json

class DashboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Check authentication
        if not self.scope["user"].is_authenticated:
            await self.close()
            return
        
        # Join dashboard group
        self.group_name = f"dashboard_{self.scope['user'].id}"
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
    
    async def dashboard_update(self, event):
        """Send dashboard update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'dashboard_update',
            'data': event['data']
        }))

# Signal handlers for real-time updates
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@receiver(post_save, sender=InfoSpot)
def info_spot_updated(sender, instance, created, **kwargs):
    """Send real-time update when info spot is created/updated"""
    channel_layer = get_channel_layer()
    
    # Notify tenant admins
    tenant_admins = TenantAdmin.objects.filter(tenant=instance.tenant)
    for admin in tenant_admins:
        async_to_sync(channel_layer.group_send)(
            f"dashboard_{admin.user.id}",
            {
                'type': 'dashboard_update',
                'data': {
                    'model': 'InfoSpot',
                    'action': 'created' if created else 'updated',
                    'object_id': instance.id,
                    'object_name': instance.name
                }
            }
        )
```

## Data Models

The dashboard uses the existing models from the multi-tenant info spots platform:

- **Tenant**: Organization management
- **TenantAdmin**: Admin user management
- **EndUser**: End user management
- **InfoSpot**: Info spot management
- **Content**: Content management
- **SpotAccess**: Analytics data
- **UserCredit**: Credit balance management
- **CreditPurchase**: Purchase transaction management
- **CreditTransaction**: Revenue tracking

### Additional Models for Dashboard

#### DashboardPreference
```python
class DashboardPreference(models.Model):
    """Store user dashboard preferences"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    layout = models.JSONField(default=dict, help_text="Dashboard layout configuration")
    items_per_page = models.IntegerField(default=25)
    default_date_range = models.IntegerField(default=30, help_text="Default date range in days")
    theme = models.CharField(max_length=20, default='light', choices=[
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('auto', 'Auto')
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

#### AuditLog
```python
class AuditLog(models.Model):
    """Track all dashboard activities"""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50)  # create, update, delete, view
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)
    object_repr = models.CharField(max_length=200)
    changes = models.JSONField(default=dict, help_text="Changed fields and values")
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.CharField(max_length=500, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['tenant', 'timestamp']),
            models.Index(fields=['model_name', 'timestamp']),
        ]
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Tenant Data Isolation in Dashboard
*For any* tenant admin user accessing the dashboard, all data displayed must belong only to their assigned tenant and must not include data from other tenants.
**Validates: Requirements 6.1, 19.1**

### Property 2: Platform Admin Full Access
*For any* platform admin (superuser) accessing the dashboard, they must have access to all tenants' data and all dashboard functionality without tenant restrictions.
**Validates: Requirements 3.1, 4.1, 5.1, 9.1, 10.1**

### Property 3: CRUD Operation Completeness
*For any* model with dashboard CRUD operations, all four operations (Create, Read, Update, Delete) must be available and functional for authorized users with appropriate data validation.
**Validates: Requirements 3.2, 3.3, 3.4, 4.2, 4.3, 4.4, 5.2, 5.3, 6.2, 6.3, 6.4, 7.2, 7.4**

### Property 4: Search and Filter Accuracy
*For any* search query or filter applied in the dashboard, the results must include all records that match the criteria and exclude all non-matching records, with consistent behavior across all models.
**Validates: Requirements 5.6, 10.5, 12.1, 12.2, 12.3, 12.4**

### Property 5: Bulk Operation Consistency
*For any* bulk operation performed on selected records, the operation must be applied to all and only the selected records, with proper progress indication and error handling.
**Validates: Requirements 6.7, 9.5, 13.1, 13.2, 13.3, 13.4, 13.5, 13.6**

### Property 6: Form Validation Enforcement
*For any* form submission in the dashboard, all validation rules must be enforced, invalid data must be rejected with specific error messages, and valid data must be processed correctly.
**Validates: Requirements 3.6, 4.5, 6.5, 7.3, 14.2, 14.5, 19.6**

### Property 7: Audit Trail Completeness
*For any* CRUD operation, bulk operation, or security event in the dashboard, a complete audit log entry must be created with user, timestamp, action, and affected data information.
**Validates: Requirements 9.6, 17.1, 17.2, 17.3, 17.4, 19.4**

### Property 8: Permission-Based Access Control
*For any* dashboard view or operation, access must be granted only to users with appropriate permissions and denied to unauthorized users, with proper authentication requirements.
**Validates: Requirements 19.1, 19.2, 19.3**

### Property 9: Real-time Update Delivery
*For any* data change made by one admin user, other admin users viewing the same data must receive real-time updates within 5 seconds, with proper conflict resolution for concurrent edits.
**Validates: Requirements 16.1, 16.2, 16.3, 16.4, 16.6**

### Property 10: Export and Import Data Accuracy
*For any* data export or import operation, the data must exactly match the source/target records, with proper validation, error reporting, and format support (CSV, Excel).
**Validates: Requirements 8.6, 11.5, 12.6, 14.1, 14.2, 14.3, 14.6, 17.5**

### Property 11: Analytics Calculation Accuracy
*For any* analytics calculation displayed in the dashboard (statistics, trends, rankings), the calculated values must exactly match the sum/count/average of the underlying data records with proper time-based filtering.
**Validates: Requirements 3.5, 6.6, 7.7, 8.1, 8.2, 8.3, 8.4, 9.3, 9.4, 10.4, 11.1, 11.2, 11.3, 11.4, 11.6**

### Property 12: Component Reusability and Consistency
*For any* UI component used in multiple dashboard views, the component must render consistently, maintain the same functionality, and provide the same user experience across all usage contexts.
**Validates: Requirements 2.1, 2.3, 2.4, 2.5**

### Property 13: Responsive Design Functionality
*For any* dashboard view accessed on different screen sizes, all functionality must remain accessible and usable without loss of features, with proper touch-friendly controls and adaptive layouts.
**Validates: Requirements 15.1, 15.2, 15.3, 15.4, 15.5, 15.6**

### Property 14: HTMX Dynamic Update Accuracy
*For any* HTMX-powered dynamic update, the updated content must accurately reflect the current state of the data without requiring a full page reload, with proper error handling and loading indicators.
**Validates: Requirements 2.6, 18.6**

### Property 15: Performance and Scalability Requirements
*For any* dashboard operation with large datasets (up to 10,000 records), the system must maintain acceptable performance through pagination, caching, lazy loading, and database optimization.
**Validates: Requirements 18.1, 18.2, 18.3, 18.4, 18.5**

### Property 16: User Preference Persistence
*For any* user customization (dashboard layout, search preferences, page sizes), the preferences must be saved per user and restored correctly across sessions and browser tabs.
**Validates: Requirements 12.5, 20.1, 20.2, 20.3, 20.4, 20.5**

### Property 17: Automatic Feature Generation
*For any* new info spot created, QR codes must be generated automatically, and for any content uploaded, proper validation and version tracking must occur automatically.
**Validates: Requirements 6.5, 7.6**

### Property 18: Credit Management Accuracy
*For any* credit-related operation (balance adjustment, purchase processing, refund), the credit calculations must be accurate, properly tracked, and reflected immediately in all relevant dashboard views.
**Validates: Requirements 5.4, 9.2, 10.3**

## Error Handling

### Error Categories

**1. Permission Errors**
- Unauthorized access: Return 403 with "Access denied" message
- Insufficient permissions: Return 403 with specific permission requirement
- Cross-tenant access: Return 403 with "Access denied to this tenant's data"

**2. Validation Errors**
- Form validation failures: Display field-specific error messages
- Bulk operation validation: Show summary of failed operations with reasons
- File upload errors: Display file format/size requirements

**3. Data Integrity Errors**
- Duplicate key violations: Show user-friendly uniqueness constraint messages
- Foreign key violations: Prevent deletion with clear dependency messages
- Concurrent modification: Show conflict resolution options

**4. HTMX Errors**
- Network failures: Show retry options with exponential backoff
- Server errors: Display generic error message and log detailed error
- Timeout errors: Show loading indicators and timeout messages

**5. Real-time Update Errors**
- WebSocket connection failures: Gracefully degrade to polling
- Message delivery failures: Retry with exponential backoff
- Authentication failures: Redirect to login

### Error Response Formats

**HTMX Error Responses**:
```json
{
  "error": {
    "type": "validation_error",
    "message": "Please correct the errors below",
    "fields": {
      "subdomain": ["This subdomain is already taken"],
      "credit_cost": ["Credit cost must be greater than 0 for paid spots"]
    }
  }
}
```

**WebSocket Error Messages**:
```json
{
  "type": "error",
  "error": {
    "code": "CONNECTION_LOST",
    "message": "Connection lost. Attempting to reconnect...",
    "retry_in": 5
  }
}
```

## Testing Strategy

### Dual Testing Approach

**Unit Tests**: Focus on individual components and functions
- Test view permissions and access control
- Test form validation and data processing
- Test component rendering and behavior
- Test utility functions and helpers

**Property-Based Tests**: Verify universal properties across all inputs
- Test correctness properties defined in this document
- Generate random valid inputs to test properties hold universally
- Minimum 100 iterations per property test
- Each property test references its design document property

### Property-Based Testing Framework

**Library**: Hypothesis for Python with Django integration

**Test Configuration**:
```python
from hypothesis import given, settings
import hypothesis.strategies as st
from hypothesis.extra.django import from_model

@settings(max_examples=100)
@given(
    user=st.builds(UserFactory),
    tenant=st.builds(TenantFactory)
)
def test_property_1_tenant_data_isolation(user, tenant):
    """
    Feature: dashboard-crud, Property 1: Tenant Data Isolation in Dashboard
    For any tenant admin user accessing the dashboard, all data displayed 
    must belong only to their assigned tenant.
    """
    # Create tenant admin
    TenantAdmin.objects.create(user=user, tenant=tenant, role='admin')
    
    # Create data for multiple tenants
    other_tenant = TenantFactory()
    InfoSpotFactory(tenant=tenant)  # Should be visible
    InfoSpotFactory(tenant=other_tenant)  # Should not be visible
    
    # Test dashboard view
    client = Client()
    client.force_login(user)
    
    with patch('apps.tenants.utils.get_current_tenant', return_value=tenant):
        response = client.get(reverse('dashboard:info_spot_list'))
        
        # Assert only tenant's data is visible
        spots_in_response = response.context['object_list']
        assert all(spot.tenant == tenant for spot in spots_in_response)
        assert not any(spot.tenant == other_tenant for spot in spots_in_response)
```

### Integration Testing

**HTMX Testing**:
```python
def test_htmx_form_submission(self):
    """Test HTMX form submission and response"""
    client = Client()
    client.force_login(self.admin_user)
    
    response = client.post(
        reverse('dashboard:tenant_create'),
        data={'name': 'Test Tenant', 'subdomain': 'test'},
        HTTP_HX_REQUEST='true'
    )
    
    self.assertEqual(response.status_code, 200)
    self.assertIn('success', response.json())
    self.assertTrue(Tenant.objects.filter(subdomain='test').exists())
```

**WebSocket Testing**:
```python
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async

@pytest.mark.asyncio
async def test_real_time_updates():
    """Test real-time dashboard updates"""
    communicator = WebsocketCommunicator(DashboardConsumer.as_asgi(), "/ws/dashboard/")
    
    # Connect
    connected, subprotocol = await communicator.connect()
    assert connected
    
    # Create info spot (should trigger update)
    await database_sync_to_async(InfoSpotFactory)()
    
    # Receive update
    response = await communicator.receive_json_from()
    assert response['type'] == 'dashboard_update'
    assert response['data']['model'] == 'InfoSpot'
    
    await communicator.disconnect()
```

## Implementation Notes

### Performance Optimizations

**Database Optimizations**:
- Use select_related() and prefetch_related() for related data
- Implement database indexes for frequently queried fields
- Use database-level pagination for large datasets
- Cache expensive analytics queries

**Frontend Optimizations**:
- Lazy load dashboard components
- Use HTMX for partial page updates
- Implement virtual scrolling for large tables
- Compress and minify static assets

**Caching Strategy**:
```python
from django.core.cache import cache
from django.views.decorators.cache import cache_page

class CachedAnalyticsView(AnalyticsView):
    def get_context_data(self, **kwargs):
        cache_key = f"analytics_{self.request.user.id}_{get_current_tenant().id}"
        cached_data = cache.get(cache_key)
        
        if not cached_data:
            cached_data = super().get_context_data(**kwargs)
            cache.set(cache_key, cached_data, timeout=300)  # 5 minutes
        
        return cached_data
```

### Security Considerations

**CSRF Protection**:
- All forms include CSRF tokens
- HTMX automatically includes CSRF headers
- API endpoints validate CSRF tokens

**Input Validation**:
- Server-side validation for all user inputs
- File upload validation (type, size, content)
- SQL injection prevention through ORM usage

**Access Control**:
- Permission checks on every view
- Tenant isolation enforcement
- Audit logging for security events

### Deployment Considerations

**Static Files**:
- Collect static files for production
- Use CDN for static asset delivery
- Implement asset versioning for cache busting

**WebSocket Configuration**:
- Configure Redis for channel layers
- Set up WebSocket routing in ASGI
- Handle WebSocket scaling across multiple servers

**Monitoring**:
- Log dashboard usage and performance metrics
- Monitor WebSocket connection health
- Track error rates and response times

## Conclusion

This design provides a comprehensive dashboard system for managing all models in the multi-tenant info spots platform. The component-based architecture ensures maintainability and reusability, while HTMX provides dynamic interactions without complex JavaScript. The system includes real-time updates, comprehensive analytics, and robust security features.

Key architectural decisions:
- Component-based UI architecture for reusability
- HTMX for dynamic interactions without JavaScript complexity
- WebSocket integration for real-time updates
- Comprehensive permission system with tenant isolation
- Property-based testing for correctness verification
- Audit logging for compliance and security
- Responsive design for mobile accessibility

The design addresses all 20 requirements with 15 testable correctness properties, comprehensive error handling, and a robust testing strategy combining unit tests and property-based tests.