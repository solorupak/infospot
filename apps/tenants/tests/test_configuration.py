"""
Unit tests for django-tenants configuration validation.
"""

from django.test import TestCase, override_settings
from django.core.exceptions import ImproperlyConfigured
from apps.tenants.validators import TenantConfigValidator


class TestDatabaseEngineValidation(TestCase):
    """Test database engine validation"""
    
    def test_correct_database_engine_passes(self):
        """Test that correct database engine passes validation"""
        database_config = {
            'default': {
                'ENGINE': 'django_tenants.postgresql_backend',
                'NAME': 'test_db',
                'USER': 'test_user',
                'PASSWORD': 'test_pass',
                'HOST': 'localhost',
                'PORT': '5432',
            }
        }
        
        with override_settings(DATABASES=database_config):
            # Should not raise any exception
            TenantConfigValidator.validate_database_config()
    
    def test_incorrect_database_engine_fails(self):
        """Test that incorrect database engine fails validation"""
        database_config = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': 'test_db',
                'USER': 'test_user',
                'PASSWORD': 'test_pass',
                'HOST': 'localhost',
                'PORT': '5432',
            }
        }
        
        with override_settings(DATABASES=database_config):
            with self.assertRaises(ImproperlyConfigured):
                TenantConfigValidator.validate_database_config()


class TestRequiredSettingsValidation(TestCase):
    """Test required settings presence"""
    
    def test_missing_tenant_model_setting_fails(self):
        """Test that missing TENANT_MODEL setting fails validation"""
        with override_settings():
            # Remove TENANT_MODEL setting
            if hasattr(override_settings, 'TENANT_MODEL'):
                delattr(override_settings, 'TENANT_MODEL')
            
            with self.assertRaises(ImproperlyConfigured):
                TenantConfigValidator.validate_tenant_settings()
    
    def test_missing_tenant_domain_model_setting_fails(self):
        """Test that missing TENANT_DOMAIN_MODEL setting fails validation"""
        with override_settings(TENANT_MODEL="tenants.Tenant"):
            # Remove TENANT_DOMAIN_MODEL setting
            if hasattr(override_settings, 'TENANT_DOMAIN_MODEL'):
                delattr(override_settings, 'TENANT_DOMAIN_MODEL')
            
            with self.assertRaises(ImproperlyConfigured):
                TenantConfigValidator.validate_tenant_settings()


class TestAppConfigurationValidation(TestCase):
    """Test app configuration validation"""
    
    def test_missing_shared_apps_setting_fails(self):
        """Test that missing SHARED_APPS setting fails validation"""
        with override_settings():
            # Remove SHARED_APPS setting
            if hasattr(override_settings, 'SHARED_APPS'):
                delattr(override_settings, 'SHARED_APPS')
            
            with self.assertRaises(ImproperlyConfigured):
                TenantConfigValidator.validate_apps()
    
    def test_missing_tenant_apps_setting_fails(self):
        """Test that missing TENANT_APPS setting fails validation"""
        with override_settings(SHARED_APPS=['django_tenants']):
            # Remove TENANT_APPS setting
            if hasattr(override_settings, 'TENANT_APPS'):
                delattr(override_settings, 'TENANT_APPS')
            
            with self.assertRaises(ImproperlyConfigured):
                TenantConfigValidator.validate_apps()
    
    def test_missing_required_shared_app_fails(self):
        """Test that missing required shared app fails validation"""
        shared_apps = [
            'django.contrib.contenttypes',
            'django.contrib.auth',
            # Missing 'django_tenants'
        ]
        
        with override_settings(SHARED_APPS=shared_apps, TENANT_APPS=[]):
            with self.assertRaises(ImproperlyConfigured):
                TenantConfigValidator.validate_apps()
    
    def test_complete_app_configuration_passes(self):
        """Test that complete app configuration passes validation"""
        shared_apps = [
            'django_tenants',
            'django.contrib.contenttypes',
            'django.contrib.auth',
        ]
        tenant_apps = [
            'django.contrib.contenttypes',
            'django.contrib.auth',
        ]
        
        with override_settings(SHARED_APPS=shared_apps, TENANT_APPS=tenant_apps):
            # Should not raise any exception
            TenantConfigValidator.validate_apps()


class TestTenantModelValidation(TestCase):
    """Test Tenant model configuration"""
    
    def test_tenant_mixin_inheritance(self):
        """Test that Tenant model inherits from TenantMixin"""
        from apps.tenants.models import Tenant
        from django_tenants.models import TenantMixin
        
        self.assertTrue(issubclass(Tenant, TenantMixin))
    
    def test_required_field_presence(self):
        """Test that all required fields are present"""
        from apps.tenants.models import Tenant
        
        required_fields = ['schema_name', 'paid_until', 'on_trial']
        for field_name in required_fields:
            with self.subTest(field=field_name):
                self.assertTrue(hasattr(Tenant, field_name))
    
    def test_tenant_model_creation(self):
        """Test that Tenant model can be created with required fields"""
        from apps.tenants.models import Tenant
        from datetime import date
        
        tenant_data = {
            'schema_name': 'test_tenant',
            'name': 'Test Tenant',
            'venue_type': 'mixed',
            'contact_email': 'test@example.com',
            'paid_until': date(2099, 12, 31),
            'on_trial': True,
        }
        
        # Should not raise any exception
        tenant = Tenant(**tenant_data)
        self.assertEqual(tenant.schema_name, 'test_tenant')
        self.assertEqual(tenant.name, 'Test Tenant')


class TestDomainModelValidation(TestCase):
    """Test Domain model configuration"""
    
    def test_domain_mixin_inheritance(self):
        """Test that Domain model inherits from DomainMixin"""
        from apps.tenants.models import Domain
        from django_tenants.models import DomainMixin
        
        self.assertTrue(issubclass(Domain, DomainMixin))
    
    def test_domain_tenant_relationship(self):
        """Test that Domain model has proper tenant relationship"""
        from apps.tenants.models import Domain
        
        # Check that tenant field exists
        self.assertTrue(hasattr(Domain, 'tenant'))
        
        # Check the field type
        tenant_field = Domain._meta.get_field('tenant')
        self.assertEqual(tenant_field.related_model.__name__, 'Tenant')