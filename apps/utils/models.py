from django.db import models
from django.conf import settings


class BaseModel(models.Model):
    """
    Abstract base model providing common fields for all models.
    Includes audit fields for tracking creation, updates, and soft deletion.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='%(class)s_created'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='%(class)s_updated'
    )
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        abstract = True