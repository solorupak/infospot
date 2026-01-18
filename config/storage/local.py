from django.core.files.storage import FileSystemStorage
from django.db import connection
from django_tenants.files.storage import TenantFileSystemStorage


class CustomLocalSchemaStorage:
    """Storage class that dynamically selects backend based on database schema."""
    
    def _get_storage_backend(self):
        """Return appropriate storage backend based on current schema."""
        schema_name = connection.schema_name
        if schema_name == "public":
            return FileSystemStorage()
        else:
            return TenantFileSystemStorage()

    def save(self, name, content, max_length=None):
        """Save file using schema-appropriate storage backend."""
        storage_backend = self._get_storage_backend()
        return storage_backend.save(name, content, max_length)

    def url(self, name):
        """Generate URL for file using schema-appropriate storage backend."""
        storage_backend = self._get_storage_backend()
        return storage_backend.url(name)
    
    def generate_filename(self, name):
        """Generate filename using schema-appropriate storage backend."""
        storage_backend = self._get_storage_backend()
        return storage_backend.generate_filename(name)

    def delete(self, name):
        """Delete filename using schema-appropriate storage backend."""
        storage_backend = self._get_storage_backend()
        return storage_backend.delete(name)
