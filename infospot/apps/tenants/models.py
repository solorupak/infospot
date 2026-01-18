from colorfield.fields import ColorField
from django.db import models
from django.utils.translation import gettext_lazy as _

from infospot.apps.utils.models import BaseModel


class SiteSetting(BaseModel):
    """Site settings for the tenants"""
    name = models.CharField(verbose_name=_("Name"), max_length=100)
    motto = models.CharField(
        verbose_name=_("Motto"), max_length=250, null=True, blank=True
    )
    logo = models.FileField(verbose_name=_("Logo"), upload_to="logo/")
    primary_color = ColorField(default="#000000")
    secondary_color = ColorField(null=True, blank=True)

    def __str__(self):
        return self.name
