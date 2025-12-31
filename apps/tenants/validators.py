from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
import importlib


class TenantConfigValidator:
    """Validates django-tenants configuration"""
    
    @staticmethod
    def validate_database_config():
        """Validate database configuration"""
        db_config = settings.DATABASES.get('default', {})
        
        if db_config.get('ENGINE') != 'django_tenants.postgresql_backend':
            raise ImproperlyConfigured(
                'DATABASE_ENGINE must be "django_tenants.postgresql_backend"'
            )
        
        required_db_fields = ['NAME', 'USER', 'PASSWORD', 'HOST', 'PORT']
        for field in required_db_fields:
            if not db_config.get(field):
                raise ImproperlyConfigured(f'Database {field} is required')
    
    @staticmethod
    def validate_tenant_settings():
        """Validate tenant-specific settings"""
        if not hasattr(settings, 'TENANT_MODEL'):
            raise ImproperlyConfigured('TENANT_MODEL setting is required')
        
        if not hasattr(settings, 'TENANT_DOMAIN_MODEL'):
            raise ImproperlyConfigured('TENANT_DOMAIN_MODEL setting is required')
        
        # Validate model imports
        try:
            tenant_model_path = settings.TENANT_MODEL
            app_label, model_name = tenant_model_path.split('.')
            importlib.import_module(f'apps.{app_label}.models')
        except (ValueError, ImportError) as e:
            raise ImproperlyConfigured(f'Invalid TENANT_MODEL: {e}')
    
    @staticmethod
    def validate_middleware():
        """Validate middleware configuration"""
        middleware = getattr(settings, 'MIDDLEWARE', [])
        
        if 'django_tenants.middleware.main.TenantMainMiddleware' not in middleware:
            raise ImproperlyConfigured(
                'TenantMainMiddleware must be in MIDDLEWARE'
            )
        
        # Check middleware order
        tenant_middleware_index = middleware.index(
            'django_tenants.middleware.main.TenantMainMiddleware'
        )
        
        if tenant_middleware_index != 0:
            raise ImproperlyConfigured(
                'TenantMainMiddleware must be the first middleware'
            )
    
    @staticmethod
    def validate_apps():
        """Validate app configuration"""
        if not hasattr(settings, 'SHARED_APPS'):
            raise ImproperlyConfigured('SHARED_APPS setting is required')
        
        if not hasattr(settings, 'TENANT_APPS'):
            raise ImproperlyConfigured('TENANT_APPS setting is required')
        
        # Validate required apps
        required_shared_apps = [
            'django_tenants',
            'django.contrib.contenttypes',
            'django.contrib.auth',
        ]
        
        for app in required_shared_apps:
            if app not in settings.SHARED_APPS:
                raise ImproperlyConfigured(f'{app} must be in SHARED_APPS')
    
    @classmethod
    def validate_all(cls):
        """Run all validations"""
        cls.validate_database_config()
        cls.validate_tenant_settings()
        cls.validate_middleware()
        cls.validate_apps()