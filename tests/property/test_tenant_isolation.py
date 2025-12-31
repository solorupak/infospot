"""
Property-based tests for tenant isolation functionality.
"""
import pytest
from hypothesis import given, settings, strategies as st
from hypothesis.extra.django import TestCase, from_model
from django.db import IntegrityError
from apps.tenants.models import Tenant, InfoSpot, TenantAdmin
from django.contrib.auth import get_user_model


class TenantIsolationPropertyTests(TestCase):
    """Property-based tests for tenant isolation"""

    @settings(max_examples=100)
    @given(
        subdomain1=st.text(
            alphabet=st.characters(whitelist_categories=('Ll', 'Nd'), whitelist_characters='-'),
            min_size=3,
            max_size=20
        ).filter(lambda x: x and not x.startswith('-') and not x.endswith('-')),
        subdomain2=st.text(
            alphabet=st.characters(whitelist_categories=('Ll', 'Nd'), whitelist_characters='-'),
            min_size=3,
            max_size=20
        ).filter(lambda x: x and not x.startswith('-') and not x.endswith('-'))
    )
    def test_property_1_tenant_subdomain_uniqueness(self, subdomain1, subdomain2):
        """
        Feature: multi-tenant-info-spots, Property 1: Tenant Subdomain Uniqueness
        For any two tenants in the system, their subdomains must be unique and 
        no two tenants can share the same subdomain identifier.
        """
        # Create first tenant
        tenant1 = Tenant.objects.create(
            subdomain=subdomain1,
            name=f"Tenant {subdomain1}",
            venue_type='public',
            contact_email=f"admin@{subdomain1}.com"
        )
        
        if subdomain1 == subdomain2:
            # Same subdomain should raise IntegrityError
            with pytest.raises(IntegrityError):
                Tenant.objects.create(
                    subdomain=subdomain2,
                    name=f"Tenant {subdomain2}",
                    venue_type='public',
                    contact_email=f"admin@{subdomain2}.com"
                )
        else:
            # Different subdomains should work fine
            tenant2 = Tenant.objects.create(
                subdomain=subdomain2,
                name=f"Tenant {subdomain2}",
                venue_type='public',
                contact_email=f"admin@{subdomain2}.com"
            )
            
            # Verify both tenants exist with unique subdomains
            assert Tenant.objects.filter(subdomain=subdomain1).count() == 1
            assert Tenant.objects.filter(subdomain=subdomain2).count() == 1
            assert tenant1.subdomain != tenant2.subdomain

    @settings(max_examples=100)
    @given(
        tenant_data=from_model(
            Tenant,
            subdomain=st.text(
                alphabet=st.characters(whitelist_categories=('Ll', 'Nd'), whitelist_characters='-'),
                min_size=3,
                max_size=20
            ).filter(lambda x: x and not x.startswith('-') and not x.endswith('-')),
            name=st.text(min_size=1, max_size=100),
            venue_type=st.sampled_from(['ticketed', 'public', 'mixed']),
            contact_email=st.emails()
        ),
        spot_name=st.text(min_size=1, max_size=100)
    )
    def test_property_2_tenant_data_isolation(self, tenant_data, spot_name):
        """
        Feature: multi-tenant-info-spots, Property 2: Tenant Data Isolation
        For any query executed within a tenant context, the results must only 
        include data belonging to that tenant and must not include data from any other tenant.
        """
        # Create two tenants
        tenant1 = Tenant.objects.create(
            subdomain=tenant_data.subdomain,
            name=tenant_data.name,
            venue_type=tenant_data.venue_type,
            contact_email=tenant_data.contact_email
        )
        
        tenant2 = Tenant.objects.create(
            subdomain=f"other-{tenant_data.subdomain}",
            name=f"Other {tenant_data.name}",
            venue_type=tenant_data.venue_type,
            contact_email=f"other-{tenant_data.contact_email}"
        )
        
        # Create info spots for each tenant
        spot1 = InfoSpot.objects.create(
            tenant=tenant1,
            name=f"{spot_name} - Tenant 1",
            access_type='free_public',
            qr_code_data=f"https://{tenant1.subdomain}.example.com/spot/1"
        )
        
        spot2 = InfoSpot.objects.create(
            tenant=tenant2,
            name=f"{spot_name} - Tenant 2",
            access_type='free_public',
            qr_code_data=f"https://{tenant2.subdomain}.example.com/spot/2"
        )
        
        # Test data isolation - each tenant should only see their own data
        tenant1_spots = InfoSpot.objects.filter(tenant=tenant1)
        tenant2_spots = InfoSpot.objects.filter(tenant=tenant2)
        
        # Verify isolation
        assert spot1 in tenant1_spots
        assert spot1 not in tenant2_spots
        assert spot2 in tenant2_spots
        assert spot2 not in tenant1_spots
        
        # Verify counts
        assert tenant1_spots.count() == 1
        assert tenant2_spots.count() == 1

    @settings(max_examples=50)  # Fewer examples for deletion test
    @given(
        tenant_data=from_model(
            Tenant,
            subdomain=st.text(
                alphabet=st.characters(whitelist_categories=('Ll', 'Nd'), whitelist_characters='-'),
                min_size=3,
                max_size=20
            ).filter(lambda x: x and not x.startswith('-') and not x.endswith('-')),
            name=st.text(min_size=1, max_size=100),
            venue_type=st.sampled_from(['ticketed', 'public', 'mixed']),
            contact_email=st.emails()
        )
    )
    def test_property_3_tenant_deletion_cascade(self, tenant_data):
        """
        Feature: multi-tenant-info-spots, Property 3: Tenant Deletion Cascade
        For any tenant that is deleted, all data associated with that tenant 
        (info spots, content, payments) must be removed, while data belonging 
        to other tenants must remain unchanged.
        """
        # Create two tenants
        tenant1 = Tenant.objects.create(
            subdomain=tenant_data.subdomain,
            name=tenant_data.name,
            venue_type=tenant_data.venue_type,
            contact_email=tenant_data.contact_email
        )
        
        tenant2 = Tenant.objects.create(
            subdomain=f"keep-{tenant_data.subdomain}",
            name=f"Keep {tenant_data.name}",
            venue_type=tenant_data.venue_type,
            contact_email=f"keep-{tenant_data.contact_email}"
        )
        
        # Create associated data for both tenants
        spot1 = InfoSpot.objects.create(
            tenant=tenant1,
            name="Spot to be deleted",
            access_type='free_public',
            qr_code_data=f"https://{tenant1.subdomain}.example.com/spot/1"
        )
        
        spot2 = InfoSpot.objects.create(
            tenant=tenant2,
            name="Spot to be kept",
            access_type='free_public',
            qr_code_data=f"https://{tenant2.subdomain}.example.com/spot/2"
        )
        
        # Create users and tenant admins
        User = get_user_model()
        user1 = User.objects.create_user(
            username=f"admin1_{tenant_data.subdomain}",
            email=f"admin1@{tenant_data.subdomain}.com"
        )
        user2 = User.objects.create_user(
            username=f"admin2_{tenant_data.subdomain}",
            email=f"admin2@{tenant_data.subdomain}.com"
        )
        
        admin1 = TenantAdmin.objects.create(
            user=user1,
            tenant=tenant1,
            role='admin'
        )
        
        admin2 = TenantAdmin.objects.create(
            user=user2,
            tenant=tenant2,
            role='admin'
        )
        
        # Record initial counts
        initial_spots_count = InfoSpot.objects.count()
        initial_admins_count = TenantAdmin.objects.count()
        
        # Delete tenant1
        tenant1_id = tenant1.id
        tenant1.delete()
        
        # Verify tenant1 and its data are deleted
        assert not Tenant.objects.filter(id=tenant1_id).exists()
        assert not InfoSpot.objects.filter(tenant_id=tenant1_id).exists()
        assert not TenantAdmin.objects.filter(tenant_id=tenant1_id).exists()
        
        # Verify tenant2 and its data remain unchanged
        assert Tenant.objects.filter(id=tenant2.id).exists()
        assert InfoSpot.objects.filter(tenant=tenant2).exists()
        assert TenantAdmin.objects.filter(tenant=tenant2).exists()
        
        # Verify specific objects
        assert not InfoSpot.objects.filter(id=spot1.id).exists()
        assert InfoSpot.objects.filter(id=spot2.id).exists()
        assert not TenantAdmin.objects.filter(id=admin1.id).exists()
        assert TenantAdmin.objects.filter(id=admin2.id).exists()
        
        # Verify counts decreased appropriately
        assert InfoSpot.objects.count() == initial_spots_count - 1
        assert TenantAdmin.objects.count() == initial_admins_count - 1