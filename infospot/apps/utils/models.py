from django.db import models
from django.utils.translation import gettext_lazy as _


class BaseModel(models.Model):
    """
    Base model that includes default created / updated timestamps.
    """
    # Timestamp fields
    created_at = models.DateTimeField(verbose_name=_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name=_('Updated at'), auto_now=True)
    deleted_at = models.DateTimeField(verbose_name=_('Deleted at'), auto_now_add=True)

    class Meta:
        abstract = True