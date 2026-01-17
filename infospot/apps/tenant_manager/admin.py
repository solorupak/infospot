from django.contrib import admin

from .models import Domain, Tenant


class TenantAdinSite(admin.AdminSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.register(Tenant)
        self.register(Domain)


tenant_admin_site = TenantAdinSite(name="tenant_admin_site")
