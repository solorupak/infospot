from django.urls import path
from . import views

app_name = 'tenants'

urlpatterns = [
    # Info spot access
    path('spot/<uuid:spot_uuid>/', views.InfoSpotAccessView.as_view(), name='spot_access'),
    
    # Credit spending
    path('spot/<uuid:spot_uuid>/spend-credits/', views.SpendCreditsView.as_view(), name='spend_credits'),
    
    # QR code download (admin only)
    path('admin/spot/<uuid:spot_uuid>/qr-code/', views.QRCodeDownloadView.as_view(), name='qr_code_download'),
    
    # Error pages
    path('tenant-not-found/', views.TenantNotFoundView.as_view(), name='tenant_not_found'),
    path('access-denied/', views.AccessDeniedView.as_view(), name='access_denied'),
]