import logging
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.db import connection, transaction
from django.conf import settings
from django_tenants.utils import get_tenant_model, get_tenant_domain_model
from apps.tenants.validators import TenantConfigValidator

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Bootstrap django-tenants system with proper migration sequence'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--create-public-tenant',
            action='store_true',
            help='Create a public tenant for shared functionality'
        )
        parser.add_argument(
            '--skip-validation',
            action='store_true',
            help='Skip configuration validation (not recommended)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without executing'
        )
    
    def handle(self, *args, **options):
        """Main bootstrap process with comprehensive error handling"""
        self.stdout.write(
            self.style.HTTP_INFO('=' * 60)
        )
        self.stdout.write(
            self.style.HTTP_INFO('Starting django-tenants bootstrap process...')
        )
        self.stdout.write(
            self.style.HTTP_INFO('=' * 60)
        )
        
        try:
            # Step 0: Pre-flight validation
            if not options['skip_validation']:
                self.stdout.write('\n📋 Step 0: Pre-flight configuration validation...')
                if not self._validate_configuration():
                    return
            else:
                self.stdout.write('\n⚠️  Skipping configuration validation (not recommended)')
            
            # Step 1: Migrate public schema first
            self.stdout.write('\n🏗️  Step 1: Migrating public schema...')
            if not self._migrate_public_schema(options['dry_run']):
                return
            
            # Step 2: Validate tenant tables exist
            self.stdout.write('\n✅ Step 2: Validating tenant tables...')
            if not self._validate_tenant_tables():
                return
            
            # Step 3: Create public tenant if requested
            if options['create_public_tenant']:
                self.stdout.write('\n🏢 Step 3: Creating public tenant...')
                if not self._create_public_tenant(options['dry_run']):
                    return
            
            # Step 4: Migrate tenant schemas
            self.stdout.write('\n🏗️  Step 4: Migrating tenant schemas...')
            if not self._migrate_tenant_schemas(options['dry_run']):
                return
            
            # Success message
            self.stdout.write('\n' + '=' * 60)
            self.stdout.write(
                self.style.SUCCESS('✅ Django-tenants bootstrap completed successfully!')
            )
            self.stdout.write(
                self.style.SUCCESS('Your multi-tenant system is ready to use.')
            )
            self.stdout.write('=' * 60)
            
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.ERROR('\n❌ Bootstrap process interrupted by user')
            )
            return
        except Exception as e:
            logger.exception("Bootstrap process failed with unexpected error")
            self.stdout.write(
                self.style.ERROR(f'\n❌ Bootstrap process failed: {e}')
            )
            self._show_recovery_instructions()
            return
    
    def _validate_configuration(self):
        """Comprehensive configuration validation"""
        try:
            self.stdout.write('   Validating database configuration...')
            TenantConfigValidator.validate_database_config()
            
            self.stdout.write('   Validating tenant settings...')
            TenantConfigValidator.validate_tenant_settings()
            
            self.stdout.write('   Validating middleware configuration...')
            TenantConfigValidator.validate_middleware()
            
            self.stdout.write('   Validating apps configuration...')
            TenantConfigValidator.validate_apps()
            
            self.stdout.write(
                self.style.SUCCESS('   ✅ All configuration validations passed')
            )
            return True
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'   ❌ Configuration validation failed: {e}')
            )
            self._show_configuration_help()
            return False
    
    def _migrate_public_schema(self, dry_run=False):
        """Migrate public schema with error handling"""
        try:
            if dry_run:
                self.stdout.write('   [DRY RUN] Would run: migrate_schemas --shared')
                return True
            
            # Check if migrations are needed first
            self.stdout.write('   Checking for pending migrations...')
            
            # Run public schema migrations
            self.stdout.write('   Running public schema migrations...')
            call_command('migrate_schemas', '--shared', verbosity=1, interactive=False)
            
            self.stdout.write(
                self.style.SUCCESS('   ✅ Public schema migration completed')
            )
            return True
            
        except Exception as e:
            logger.error(f"Public schema migration failed: {e}")
            self.stdout.write(
                self.style.ERROR(f'   ❌ Public schema migration failed: {e}')
            )
            self._show_migration_help('public')
            return False
    
    def _validate_tenant_tables(self):
        """Validate that tenant tables exist in public schema"""
        try:
            with connection.cursor() as cursor:
                # Check if tenants_tenant table exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'tenants_tenant'
                    );
                """)
                tenant_table_exists = cursor.fetchone()[0]
                
                # Check if tenants_domain table exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'tenants_domain'
                    );
                """)
                domain_table_exists = cursor.fetchone()[0]
                
                if not tenant_table_exists:
                    self.stdout.write(
                        self.style.ERROR('   ❌ tenants_tenant table does not exist')
                    )
                    return False
                
                if not domain_table_exists:
                    self.stdout.write(
                        self.style.ERROR('   ❌ tenants_domain table does not exist')
                    )
                    return False
                
                self.stdout.write(
                    self.style.SUCCESS('   ✅ Tenant tables exist in public schema')
                )
                return True
                
        except Exception as e:
            logger.error(f"Tenant table validation failed: {e}")
            self.stdout.write(
                self.style.ERROR(f'   ❌ Tenant table validation failed: {e}')
            )
            return False
    
    def _create_public_tenant(self, dry_run=False):
        """Create a public tenant for shared functionality"""
        try:
            if dry_run:
                self.stdout.write('   [DRY RUN] Would create public tenant')
                return True
            
            TenantModel = get_tenant_model()
            DomainModel = get_tenant_domain_model()
            
            # Create public tenant with transaction
            with transaction.atomic():
                tenant, created = TenantModel.objects.get_or_create(
                    schema_name='public',
                    defaults={
                        'name': 'Public Tenant',
                        'venue_type': 'public',
                        'contact_email': 'admin@example.com',
                        'paid_until': '2099-12-31',
                        'on_trial': False,
                    }
                )
                
                if created:
                    # Create domain for public tenant
                    domain, domain_created = DomainModel.objects.get_or_create(
                        domain='localhost',
                        defaults={
                            'tenant': tenant,
                            'is_primary': True
                        }
                    )
                    
                    self.stdout.write(
                        self.style.SUCCESS('   ✅ Public tenant created successfully')
                    )
                else:
                    self.stdout.write('   ℹ️  Public tenant already exists')
                
                return True
                
        except Exception as e:
            logger.error(f"Public tenant creation failed: {e}")
            self.stdout.write(
                self.style.ERROR(f'   ❌ Failed to create public tenant: {e}')
            )
            return False
    
    def _migrate_tenant_schemas(self, dry_run=False):
        """Migrate tenant schemas with error handling"""
        try:
            if dry_run:
                self.stdout.write('   [DRY RUN] Would run: migrate_schemas')
                return True
            
            # Check if any tenants exist
            TenantModel = get_tenant_model()
            tenant_count = TenantModel.objects.count()
            
            if tenant_count == 0:
                self.stdout.write('   ℹ️  No tenants exist, skipping tenant schema migrations')
                return True
            
            self.stdout.write(f'   Found {tenant_count} tenant(s), migrating schemas...')
            
            # Run tenant schema migrations
            call_command('migrate_schemas', verbosity=1, interactive=False)
            
            self.stdout.write(
                self.style.SUCCESS('   ✅ Tenant schema migrations completed')
            )
            return True
            
        except Exception as e:
            logger.error(f"Tenant schema migration failed: {e}")
            self.stdout.write(
                self.style.ERROR(f'   ❌ Tenant schema migration failed: {e}')
            )
            self._show_migration_help('tenant')
            return False
    
    def _show_configuration_help(self):
        """Show configuration help and common fixes"""
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.WARNING('Configuration Help'))
        self.stdout.write('=' * 50)
        self.stdout.write('Common configuration issues and fixes:')
        self.stdout.write('')
        self.stdout.write('1. Database Engine:')
        self.stdout.write('   DATABASES["default"]["ENGINE"] = "django_tenants.postgresql_backend"')
        self.stdout.write('')
        self.stdout.write('2. Required Settings:')
        self.stdout.write('   TENANT_MODEL = "tenants.Tenant"')
        self.stdout.write('   TENANT_DOMAIN_MODEL = "tenants.Domain"')
        self.stdout.write('')
        self.stdout.write('3. Middleware (must be first):')
        self.stdout.write('   MIDDLEWARE = ["django_tenants.middleware.main.TenantMainMiddleware", ...]')
        self.stdout.write('')
        self.stdout.write('4. Apps Configuration:')
        self.stdout.write('   SHARED_APPS = ["django_tenants", "django.contrib.contenttypes", ...]')
        self.stdout.write('   TENANT_APPS = [...]')
        self.stdout.write('')
        self.stdout.write('For detailed configuration, see the django-tenants documentation.')
        self.stdout.write('=' * 50)
    
    def _show_migration_help(self, migration_type):
        """Show migration-specific help"""
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.WARNING(f'{migration_type.title()} Migration Help'))
        self.stdout.write('=' * 50)
        
        if migration_type == 'public':
            self.stdout.write('Public schema migration failed. Try these steps:')
            self.stdout.write('')
            self.stdout.write('1. Check if you have pending migrations:')
            self.stdout.write('   python manage.py showmigrations')
            self.stdout.write('')
            self.stdout.write('2. Create missing migrations:')
            self.stdout.write('   python manage.py makemigrations')
            self.stdout.write('')
            self.stdout.write('3. Run public schema migration manually:')
            self.stdout.write('   python manage.py migrate_schemas --shared')
            self.stdout.write('')
            self.stdout.write('4. If database is corrupted, consider:')
            self.stdout.write('   python manage.py reset_migrations (if available)')
            
        elif migration_type == 'tenant':
            self.stdout.write('Tenant schema migration failed. Try these steps:')
            self.stdout.write('')
            self.stdout.write('1. Ensure public schema is migrated first')
            self.stdout.write('2. Check if tenants exist:')
            self.stdout.write('   python manage.py shell -c "from apps.tenants.models import Tenant; print(Tenant.objects.count())"')
            self.stdout.write('')
            self.stdout.write('3. Run tenant migration manually:')
            self.stdout.write('   python manage.py migrate_schemas')
            self.stdout.write('')
            self.stdout.write('4. Create a tenant first if none exist:')
            self.stdout.write('   python manage.py create_tenant')
        
        self.stdout.write('=' * 50)
    
    def _show_recovery_instructions(self):
        """Show recovery instructions for failed bootstrap"""
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.ERROR('Bootstrap Recovery Instructions'))
        self.stdout.write('=' * 60)
        self.stdout.write('The bootstrap process failed. Here are recovery options:')
        self.stdout.write('')
        self.stdout.write('1. Fix configuration issues and retry:')
        self.stdout.write('   python manage.py bootstrap_tenants')
        self.stdout.write('')
        self.stdout.write('2. Skip validation if you\'re sure config is correct:')
        self.stdout.write('   python manage.py bootstrap_tenants --skip-validation')
        self.stdout.write('')
        self.stdout.write('3. Run a dry-run to see what would happen:')
        self.stdout.write('   python manage.py bootstrap_tenants --dry-run')
        self.stdout.write('')
        self.stdout.write('4. For complete reset (DANGER - will lose data):')
        self.stdout.write('   python manage.py reset_migrations  # if available')
        self.stdout.write('')
        self.stdout.write('5. Manual step-by-step approach:')
        self.stdout.write('   a) python manage.py migrate_schemas --shared')
        self.stdout.write('   b) python manage.py create_tenant')
        self.stdout.write('   c) python manage.py migrate_schemas')
        self.stdout.write('')
        self.stdout.write('For more help, check the logs or contact support.')
        self.stdout.write('=' * 60)