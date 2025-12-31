from django.core.management.base import BaseCommand
from django_tenants.utils import get_tenant_model, get_tenant_domain_model
import re


class Command(BaseCommand):
    help = 'Create a new tenant with domain'
    
    def add_arguments(self, parser):
        parser.add_argument('schema_name', type=str, help='Tenant schema name')
        parser.add_argument('domain_name', type=str, help='Domain name for tenant')
        parser.add_argument('--name', type=str, help='Tenant display name')
        parser.add_argument('--email', type=str, help='Contact email')
        parser.add_argument('--venue-type', type=str, default='mixed', 
                          choices=['ticketed', 'public', 'mixed'])
    
    def handle(self, *args, **options):
        schema_name = options['schema_name']
        domain_name = options['domain_name']
        
        # Validate schema name
        if not self.validate_schema_name(schema_name):
            return
        
        try:
            TenantModel = get_tenant_model()
            DomainModel = get_tenant_domain_model()
            
            # Create tenant
            tenant = TenantModel.objects.create(
                schema_name=schema_name,
                name=options.get('name', schema_name.title()),
                venue_type=options['venue_type'],
                contact_email=options.get('email', f'admin@{domain_name}'),
                paid_until='2099-12-31',
                on_trial=True,
            )
            
            # Create domain
            DomainModel.objects.create(
                domain=domain_name,
                tenant=tenant,
                is_primary=True
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Tenant "{schema_name}" created successfully')
            )
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to create tenant: {e}'))
    
    def validate_schema_name(self, schema_name):
        """Validate schema name format"""
        if not re.match(r'^[a-z][a-z0-9_]*$', schema_name):
            self.stdout.write(
                self.style.ERROR(
                    'Schema name must start with lowercase letter and contain only '
                    'lowercase letters, numbers, and underscores'
                )
            )
            return False
        
        if schema_name in ['public', 'information_schema', 'pg_catalog']:
            self.stdout.write(
                self.style.ERROR(f'Schema name "{schema_name}" is reserved')
            )
            return False
        
        return True