"""
Property-based tests for django-tenants configuration validation.

Feature: django-tenants-migration
"""

from django.test import TestCase, override_settings
from django.core.exceptions import ImproperlyConfigured
from hypothesis import given, strategies as st
from apps.tenants.validators import TenantConfigValidator


class TestDatabaseConfigurationValidation(TestCase):
    """
    Property 6: Database Configuration Validation
    For any django-tenants setup, the database engine must be django_tenants.postgresql_backend 
    and all required settings must be present.
    Validates: Requirements 4.1, 4.5
    """
    
    @given(
        engine=st.text(min_size=1).filter(lambda x: x != 'django_tenants.postgresql_backend'),
        name=st.text(min_size=1),
        user=st.text(min_size=1),
        password=st.text(min_size=1),
        host=st.text(min_size=1),
        port=st.text(min_size=1)
    )
    def test_invalid_database_engine_raises_error(self, engine, name, user, password, host, port):
        """For any database configuration with invalid engine, validation must fail"""
        database_config = {
            'default': {
                'ENGINE': engine,
                'NAME': name,
                'USER': user,
                'PASSWORD': password,
                'HOST': host,
                'PORT': port,
            }
        }
        
        with override_settings(DATABASES=database_config):
            with self.assertRaises(ImproperlyConfigured) as cm:
                TenantConfigValidator.validate_database_config()
            
            self.assertIn('django_tenants.postgresql_backend', str(cm.exception))
    
    @given(
        name=st.text(min_size=1),
        user=st.text(min_size=1),
        password=st.text(min_size=1),
        host=st.text(min_size=1),
        port=st.text(min_size=1)
    )
    def test_valid_database_engine_passes_validation(self, name, user, password, host, port):
        """For any database configuration with correct engine, validation must pass"""
        database_config = {
            'default': {
                'ENGINE': 'django_tenants.postgresql_backend',
                'NAME': name,
                'USER': user,
                'PASSWORD': password,
                'HOST': host,
                'PORT': port,
            }
        }
        
        with override_settings(DATABASES=database_config):
            # Should not raise any exception
            try:
                TenantConfigValidator.validate_database_config()
            except ImproperlyConfigured:
                self.fail("validate_database_config raised ImproperlyConfigured unexpectedly")
    
    @given(
        missing_field=st.sampled_from(['NAME', 'USER', 'PASSWORD', 'HOST', 'PORT'])
    )
    def test_missing_required_database_field_raises_error(self, missing_field):
        """For any database configuration missing required fields, validation must fail"""
        complete_config = {
            'ENGINE': 'django_tenants.postgresql_backend',
            'NAME': 'test_db',
            'USER': 'test_user',
            'PASSWORD': 'test_pass',
            'HOST': 'localhost',
            'PORT': '5432',
        }
        
        # Remove the specified field
        incomplete_config = {k: v for k, v in complete_config.items() if k != missing_field}
        
        database_config = {'default': incomplete_config}
        
        with override_settings(DATABASES=database_config):
            with self.assertRaises(ImproperlyConfigured) as cm:
                TenantConfigValidator.validate_database_config()
            
            self.assertIn(missing_field, str(cm.exception))


class TestMiddlewareConfigurationValidation(TestCase):
    """
    Property 7: Middleware Configuration Validation
    For any django-tenants application, TenantMainMiddleware must be the first middleware 
    in the MIDDLEWARE list.
    Validates: Requirements 4.3
    """
    
    @given(
        other_middleware=st.lists(
            st.text(min_size=1).filter(
                lambda x: x != 'django_tenants.middleware.main.TenantMainMiddleware'
            ),
            min_size=1,
            max_size=10
        )
    )
    def test_missing_tenant_middleware_raises_error(self, other_middleware):
        """For any middleware list without TenantMainMiddleware, validation must fail"""
        with override_settings(MIDDLEWARE=other_middleware):
            with self.assertRaises(ImproperlyConfigured) as cm:
                TenantConfigValidator.validate_middleware()
            
            self.assertIn('TenantMainMiddleware must be in MIDDLEWARE', str(cm.exception))
    
    @given(
        prefix_middleware=st.lists(
            st.text(min_size=1).filter(
                lambda x: x != 'django_tenants.middleware.main.TenantMainMiddleware'
            ),
            min_size=1,
            max_size=5
        ),
        suffix_middleware=st.lists(
            st.text(min_size=1).filter(
                lambda x: x != 'django_tenants.middleware.main.TenantMainMiddleware'
            ),
            min_size=0,
            max_size=5
        )
    )
    def test_tenant_middleware_not_first_raises_error(self, prefix_middleware, suffix_middleware):
        """For any middleware list with TenantMainMiddleware not first, validation must fail"""
        middleware_list = (
            prefix_middleware + 
            ['django_tenants.middleware.main.TenantMainMiddleware'] + 
            suffix_middleware
        )
        
        with override_settings(MIDDLEWARE=middleware_list):
            with self.assertRaises(ImproperlyConfigured) as cm:
                TenantConfigValidator.validate_middleware()
            
            self.assertIn('must be the first middleware', str(cm.exception))
    
    @given(
        suffix_middleware=st.lists(
            st.text(min_size=1).filter(
                lambda x: x != 'django_tenants.middleware.main.TenantMainMiddleware'
            ),
            min_size=0,
            max_size=10
        )
    )
    def test_tenant_middleware_first_passes_validation(self, suffix_middleware):
        """For any middleware list with TenantMainMiddleware first, validation must pass"""
        middleware_list = ['django_tenants.middleware.main.TenantMainMiddleware'] + suffix_middleware
        
        with override_settings(MIDDLEWARE=middleware_list):
            # Should not raise any exception
            try:
                TenantConfigValidator.validate_middleware()
            except ImproperlyConfigured:
                self.fail("validate_middleware raised ImproperlyConfigured unexpectedly")


class TestTenantModelConfigurationValidation(TestCase):
    """
    Property 4: Tenant Model Configuration Validation
    For any Tenant model, it must inherit from TenantMixin and include all required fields 
    (schema_name, paid_until, on_trial).
    Validates: Requirements 3.1, 3.3
    """
    
    def test_tenant_model_inherits_from_tenant_mixin(self):
        """For any Tenant model, it must inherit from TenantMixin"""
        from apps.tenants.models import Tenant
        from django_tenants.models import TenantMixin
        
        # Check that Tenant inherits from TenantMixin
        self.assertTrue(issubclass(Tenant, TenantMixin))
    
    @given(
        required_field=st.sampled_from(['schema_name', 'paid_until', 'on_trial'])
    )
    def test_tenant_model_has_required_fields(self, required_field):
        """For any required field, the Tenant model must have it"""
        from apps.tenants.models import Tenant
        
        # Check that the required field exists
        self.assertTrue(hasattr(Tenant, required_field))
    
    def test_tenant_model_has_auto_create_schema_setting(self):
        """For any Tenant model, it must have auto_create_schema setting"""
        from apps.tenants.models import Tenant
        
        # Check that auto_create_schema is set
        self.assertTrue(hasattr(Tenant, 'auto_create_schema'))
        self.assertTrue(Tenant.auto_create_schema)
    
    def test_tenant_model_has_auto_drop_schema_setting(self):
        """For any Tenant model, it must have auto_drop_schema setting"""
        from apps.tenants.models import Tenant
        
        # Check that auto_drop_schema is set
        self.assertTrue(hasattr(Tenant, 'auto_drop_schema'))
        self.assertFalse(Tenant.auto_drop_schema)  # Should be False for safety


class TestDomainModelConfigurationValidation(TestCase):
    """
    Property 5: Domain Model Configuration Validation
    For any Domain model, it must inherit from DomainMixin and be properly linked to the Tenant model.
    Validates: Requirements 3.2
    """
    
    def test_domain_model_inherits_from_domain_mixin(self):
        """For any Domain model, it must inherit from DomainMixin"""
        from apps.tenants.models import Domain
        from django_tenants.models import DomainMixin
        
        # Check that Domain inherits from DomainMixin
        self.assertTrue(issubclass(Domain, DomainMixin))
    
    def test_domain_model_has_tenant_relationship(self):
        """For any Domain model, it must be properly linked to Tenant model"""
        from apps.tenants.models import Domain
        
        # Check that Domain has tenant field (inherited from DomainMixin)
        self.assertTrue(hasattr(Domain, 'tenant'))
        
        # Check that the relationship is properly configured
        tenant_field = Domain._meta.get_field('tenant')
        self.assertEqual(tenant_field.related_model.__name__, 'Tenant')