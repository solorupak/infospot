#!/usr/bin/env python3
"""
Django-Tenants Bootstrap Script

This script helps bootstrap the django-tenants system with proper migration sequence.
Run this after activating your virtual environment and ensuring Django is available.

Usage:
    python bootstrap_django_tenants.py
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

def main():
    """Bootstrap django-tenants system"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
    
    try:
        django.setup()
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    
    print("🚀 Starting Django-Tenants Bootstrap Process...")
    print("=" * 50)
    
    # Step 1: Validate configuration
    print("\n📋 Step 1: Validating django-tenants configuration...")
    try:
        execute_from_command_line(['manage.py', 'validate_tenant_config'])
        print("✅ Configuration validation passed!")
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        print("Please fix the configuration issues before proceeding.")
        return False
    
    # Step 2: Run bootstrap command
    print("\n🔧 Step 2: Running bootstrap command...")
    try:
        execute_from_command_line(['manage.py', 'bootstrap_tenants', '--create-public-tenant'])
        print("✅ Bootstrap completed successfully!")
    except Exception as e:
        print(f"❌ Bootstrap failed: {e}")
        return False
    
    # Step 3: Create a sample tenant
    print("\n🏢 Step 3: Creating sample tenant...")
    try:
        execute_from_command_line([
            'manage.py', 'create_tenant', 
            'museum', 'museum.localhost',
            '--name', 'Museum Demo',
            '--email', 'admin@museum.localhost',
            '--venue-type', 'mixed'
        ])
        print("✅ Sample tenant created successfully!")
    except Exception as e:
        print(f"⚠️  Sample tenant creation failed: {e}")
        print("You can create tenants manually later using:")
        print("python manage.py create_tenant <schema_name> <domain_name>")
    
    print("\n🎉 Django-Tenants Bootstrap Complete!")
    print("=" * 50)
    print("Next steps:")
    print("1. Your django-tenants system is now ready")
    print("2. You can create additional tenants using: python manage.py create_tenant")
    print("3. Access your tenants via their configured domains")
    print("4. Run migrations for tenant schemas as needed")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)