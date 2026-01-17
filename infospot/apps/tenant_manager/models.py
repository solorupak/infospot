from django.db import models
from django_tenants.models import TenantMixin, DomainMixin
from django.utils.translation import gettext_lazy as _

from infospot.apps.utils.models import BaseModel


class Tenant(TenantMixin, BaseModel):
    name = models.CharField(
        verbose_name=_("Name"),
        max_length=100
    )
    paid_until = models.DateField(verbose_name=_("Paid until"))
    on_trial = models.BooleanField(verbose_name=_("On trial"))

    auto_create_schema = True


class Domain(DomainMixin):
    pass