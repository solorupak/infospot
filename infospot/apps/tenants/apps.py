from django.apps import AppConfig


class TenantsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "infospot.apps.tenants"
    label = "tenants"

    def ready(self):
        """
        Override this method in subclasses to run code when Django starts.
        """
