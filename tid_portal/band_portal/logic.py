from django.db import models
from django.utils.translation import gettext_lazy as _


class StatusChoices(models.TextChoices):
    NOTDONE = 'ND', _('Not done yet')
    MUSTREDONE = 'MRD', _('Demo ready, must redone')
    DONE = 'D', _('Done')

