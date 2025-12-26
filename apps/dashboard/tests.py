from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.tenants.models import Tenant, TenantAdmin

User = get_user_model()


class DashboardBaseViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.tenant = Tenant.objects.create(
            subdomain='test',
            name='Test Tenant',
            venue_type='public',
            contact_email='admin@test.com'
        )
        
    def test_dashboard_requires_login(self):
        """Test that dashboard requires authentication"""
        response = self.client.get(reverse('dashboard:home'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
    def test_dashboard_denies_regular_user(self):
        """Test that regular users cannot access dashboard"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('dashboard:home'))
        self.assertEqual(response.status_code, 403)  # Permission denied
        
    def test_dashboard_allows_tenant_admin(self):
        """Test that tenant admins can access dashboard"""
        TenantAdmin.objects.create(
            user=self.user,
            tenant=self.tenant,
            role='admin'
        )
        self.client.force_login(self.user)
        response = self.client.get(reverse('dashboard:home'))
        self.assertEqual(response.status_code, 200)
        
    def test_dashboard_allows_superuser(self):
        """Test that superusers can access dashboard"""
        superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.client.force_login(superuser)
        response = self.client.get(reverse('dashboard:home'))
        self.assertEqual(response.status_code, 200)
        
    def test_dashboard_context_data(self):
        """Test that dashboard provides correct context data"""
        TenantAdmin.objects.create(
            user=self.user,
            tenant=self.tenant,
            role='admin'
        )
        self.client.force_login(self.user)
        
        # Mock get_current_tenant to return our test tenant
        with self.settings(MIDDLEWARE=['apps.tenants.middleware.TenantMiddleware']):
            response = self.client.get(reverse('dashboard:home'))
            
        self.assertEqual(response.status_code, 200)
        self.assertIn('dashboard_nav', response.context)
        self.assertIn('is_platform_admin', response.context)
        self.assertFalse(response.context['is_platform_admin'])  # Regular tenant admin