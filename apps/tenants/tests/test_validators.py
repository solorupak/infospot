"""
Unit tests for TenantConfigValidator.
"""

from django.test import TestCase, override_settings
from django.core.exceptions import ImproperlyConfigured
from apps.tenants.validators import TenantConfigValidator


class TestTenantConfigValidatorDatabaseConfig(TestCase):
    """Test database configuration validation methods"""
    
    def test_validate_database_config_success(self):
        """Test successful database configuration validation"""
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
    
    def test_validate_database_config_wrong_engine(self):
        """Test database configuration validation with wrong engine"""
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
            with self.assertRaises(ImproperlyConfigured) as cm:
                TenantConfigValidator.validate_database_config()
            
            self.assertIn('django_tenants.postgresql_backend', str(cm.exception))
    
    def test_validate_database_config_missing_fields(self):
        """Test database configuration validation with missing required fields"""
        required_fields = ['NAME', 'USER', 'PASSWORD', 'HOST', 'PORT']
        
        for missing_field in required_fields:
            with self.subTest(missing_field=missing_field):
                complete_config = {
                    'ENGINE': 'django_tenants.postgresql_backend',
                    'NAME': 'test_db',
                    'USER': 'test_user',
                    'PASSWORD': 'test_pass',
                    'HOST': 'localhost',
                    'PORT': '5432',
                }
                
                # Remove the field
                del complete_config[missing_field]
                database_config = {'default': complete_config}
                
                with override_settings(DATABASES=database_config):
                    with self.assertRaises(ImproperlyConfigured) as cm:
                        TenantConfigValidator.validate_database_config()
                    
                    self.assertIn(missing_field, str(cm.exception))


class TestTenantConfigValidatorTenantSettings(TestCase):
    """Test tenant settings validation methods"""
    
    def test_validate_tenant_settings_success(self):
        """Test successful tenant settings validation"""
        with override_settings(
            TENANT_MODEL='tenants.Tenant',
            TENANT_DOMAIN_MODEL='tenants.Domain'
        ):
            # Should not raise any exception
            TenantConfigValidator.validate_tenant_settings()
    
    def test_validate_tenant_settings_missing_tenant_model(self):
        """Test tenant settings validation with missing TENANT_MODEL"""
        with override_settings():
            # Remove TENANT_MODEL if it exists
            if hasattr(override_settings, 'TENANT_MODEL'):
                delattr(override_settings, 'TENANT_MODEL')
            
            with self.assertRaises(ImproperlyConfigured) as cm:
                TenantConfigValidator.validate_tenant_settings()
            
            self.assertIn('TENANT_MODEL', str(cm.exception))
    
    def test_validate_tenant_settings_missing_domain_model(self):
        """Test tenant settings validation with missing TENANT_DOMAIN_MODEL"""
        with override_settings(TENANT_MODEL='tenants.Tenant'):
            # Remove TENANT_DOMAIN_MODEL if it exists
            if hasattr(override_settings, 'TENANT_DOMAIN_MODEL'):
                delattr(override_settings, 'TENANT_DOMAIN_MODEL')
            
            with self.assertRaises(ImproperlyConfigured) as cm:
                TenantConfigValidator.validate_tenant_settings()
            
            self.assertIn('TENANT_DOMAIN_MODEL', str(cm.exception))


class TestTenantConfigValidatorMiddleware(TestCase):
    """Test middleware configuration validation methods"""
    
    def test_validate_middleware_success(self):
        """Test successful middleware validation"""
        middleware = [
            'django_tenants.middleware.main.TenantMainMiddleware',
            'django.middleware.security.SecurityMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
        ]
        
        with override_settings(MIDDLEWARE=middleware):
            # Should not raise any exception
            TenantConfigValidator.validate_middleware()
    
    def test_validate_middleware_missing_tenant_middleware(self):
        """Test middleware validation with missing TenantMainMiddleware"""
        middleware = [
            'django.middleware.security.SecurityMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
        ]
        
        with override_settings(MIDDLEWARE=middleware):
            with self.assertRaises(ImproperlyConfigured) as cm:
                TenantConfigValidator.validate_middleware()
            
            self.assertIn('TenantMainMiddleware must be in MIDDLEWARE', str(cm.exception))
    
    def test_validate_middleware_wrong_order(self):
        """Test middleware validation with TenantMainMiddleware not first"""
        middleware = [
            'django.middleware.security.SecurityMiddleware',
            'django_tenants.middleware.main.TenantMainMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
        ]
        
        with override_settings(MIDDLEWARE=middleware):
            with self.assertRaises(ImproperlyConfigured) as cm:
                TenantConfigValidator.validate_middleware()
            
            self.assertIn('must be the first middleware', str(cm.exception))


class TestTenantConfigValidatorApps(TestCase):
    """Test apps configuration validation methods"""
    
    def test_validate_apps_success(self):
        """Test successful apps validation"""
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
    
    def test_validate_apps_missing_shared_apps(self):
        """Test apps validation with missing SHARED_APPS"""
        with override_settings():
            # Remove SHARED_APPS if it exists
            if hasattr(override_settings, 'SHARED_APPS'):
                delattr(override_settings, 'SHARED_APPS')
            
            with self.assertRaises(ImproperlyConfigured) as cm:
                TenantConfigValidator.validate_apps()
            
            self.assertIn('SHARED_APPS', str(cm.exception))
    
    def test_validate_apps_missing_tenant_apps(self):
        """Test apps validation with missing TENANT_APPS"""
        with override_settings(SHARED_APPS=['django_tenants']):
            # Remove TENANT_APPS if it exists
            if hasattr(override_settings, 'TENANT_APPS'):
                delattr(override_settings, 'TENANT_APPS')
            
            with self.assertRaises(ImproperlyConfigured) as cm:
                TenantConfigValidator.validate_apps()
            
            self.assertIn('TENANT_APPS', str(cm.exception))
    
    def test_validate_apps_missing_required_shared_app(self):
        """Test apps validation with missing required shared apps"""
        required_apps = [
            'django_tenants',
            'django.contrib.contenttypes',
            'django.contrib.auth',
        ]
        
        for missing_app in required_apps:
            with self.subTest(missing_app=missing_app):
                shared_apps = [app for app in required_apps if app != missing_app]
                
                with override_settings(SHARED_APPS=shared_apps, TENANT_APPS=[]):
                    with self.assertRaises(ImproperlyConfigured) as cm:
                        TenantConfigValidator.validate_apps()
                    
                    self.assertIn(missing_app, str(cm.exception))


class TestTenantConfigValidatorAll(TestCase):
    """Test complete validation method"""
    
    def test_validate_all_success(self):
        """Test that validate_all runs all validations successfully"""
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
        
        middleware = [
            'django_tenants.middleware.main.TenantMainMiddleware',
            'django.middleware.security.SecurityMiddleware',
        ]
        
        shared_apps = [
            'django_tenants',
            'django.contrib.contenttypes',
            'django.contrib.auth',
        ]
        
        tenant_apps = [
            'django.contrib.contenttypes',
            'django.contrib.auth',
        ]
        
        with override_settings(
            DATABASES=database_config,
            MIDDLEWARE=middleware,
            SHARED_APPS=shared_apps,
            TENANT_APPS=tenant_apps,
            TENANT_MODEL='tenants.Tenant',
            TENANT_DOMAIN_MODEL='tenants.Domain'
        ):
            # Should not raise any exception
            TenantConfigValidator.validate_all()
    
    def test_validate_all_failure_propagates(self):
        """Test that validate_all propagates validation failures"""
        # Use invalid database engine to trigger failure
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
                TenantConfigValidator.validate_all()