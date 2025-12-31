from django.core.management.base import BaseCommand
from apps.tenants.validators import TenantConfigValidator


class Command(BaseCommand):
    help = 'Validate django-tenants configuration'
    
    def handle(self, *args, **options):
        self.stdout.write('Validating django-tenants configuration...')
        
        try:
            TenantConfigValidator.validate_all()
            self.stdout.write(
                self.style.SUCCESS('All django-tenants configuration checks passed!')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Configuration validation failed: {e}')
            )
            return
        
        self.stdout.write('Configuration validation completed successfully.')