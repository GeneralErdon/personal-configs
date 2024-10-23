from typing import Any
from django.db import models
import datetime as dt

class BaseManager(models.Manager):
    """
    Base manager for Base models
    """
    def get_deactivated_status(self) -> bool | Any:
        """
        Returns the deactivated status value that represents a deactivated record
        """
        return self.model.deactivated_status
    
    def active_objects(self):
        """
        returns a queryset of all NOT deleted objects
        """
        return self.get_queryset().exclude(status=self.get_deactivated_status())