#!/usr/bin/env python3
"""
Script to add additional packages for the multi-tenant info spots platform
"""

import subprocess
import sys

# Additional packages for multi-tenant info spots platform
packages_to_add = [
    # Multi-tenancy support
    "django-tenant-schemas",  # For multi-tenant architecture
    
    # Enhanced UI/UX
    "django-htmx",           # For dynamic UI updates without page reloads
    "django-bootstrap5",     # Bootstrap 5 integration (you have crispy-bootstrap5)
    
    # File storage and media handling
    "django-storages[boto3]", # For cloud storage (S3) support
    
    # Geographic and internationalization
    "django-countries",      # Country field support
    "django-phonenumber-field[phonenumbers]", # Phone number validation
    
    # Enhanced development tools
    "django-extensions",     # Additional Django management commands
    
    # Audio processing (for audio content optimization)
    "pydub",                # Audio file processing
    
    # Enhanced image processing
    "pillow-simd",          # Faster image processing (replaces pillow)
    
    # API enhancements
    "django-filter",        # Advanced filtering for APIs
    "django-rest-auth",     # REST authentication
    
    # Caching and performance
    "django-cachalot",      # ORM caching
    
    # Security enhancements
    "django-csp",           # Content Security Policy
    "django-permissions-policy", # Permissions Policy headers
    
    # Monitoring and logging
    "django-health-check",  # Health check endpoints
    
    # Testing enhancements
    "factory-boy",          # Test data factories (already in dev dependencies)
    "pytest-mock",          # Mocking for tests
]

def run_uv_add(packages):
    """Run uv add command for the given packages"""
    try:
        # Replace pillow with pillow-simd
        cmd = ["uv", "add"] + packages + ["--replace", "pillow"]
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Packages added successfully!")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error adding packages: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return False

if __name__ == "__main__":
    print("🚀 Adding additional packages for multi-tenant info spots platform...")
    print(f"📦 Packages to add: {', '.join(packages_to_add)}")
    
    success = run_uv_add(packages_to_add)
    
    if success:
        print("\n✅ All packages added successfully!")
        print("\n📋 Next steps:")
        print("1. Update your Django settings to configure the new packages")
        print("2. Run migrations if needed")
        print("3. Update your requirements.txt if you're using it for deployment")
    else:
        print("\n❌ Some packages failed to install. Check the errors above.")
        sys.exit(1)