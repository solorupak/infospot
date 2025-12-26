from django.urls import path, include
from .views.base import DashboardBaseView

app_name = 'dashboard'

urlpatterns = [
    path('', DashboardBaseView.as_view(), name='home'),
    # Model-specific URL patterns will be added here
    # path('tenants/', include('apps.dashboard.views.tenant_urls')),
    # path('info-spots/', include('apps.dashboard.views.info_spot_urls')),
    # etc.
]