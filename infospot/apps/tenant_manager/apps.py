from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsersConfig(AppConfig):
    name = "infospot.apps.tenant_manager"
    label="tenant_manager"
    verbose_name = _("TenantManager")

    def ready(self):
        """
        Override this method in subclasses to run code when Django starts.
        """
