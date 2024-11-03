from typing import Any, Iterable
from django.db.models.manager import Manager

class BaseManager(Manager):
    """
    Base manager for Base models
    """
    def _get_deactivated_status(self) -> bool | Any:
        """
        Returns the deactivated status value that represents a deactivated record
        """
        return self.model.deactivated_status
    
    def active_objects(self):
        """
        returns a queryset of all NOT deleted objects
        """
        return self.get_queryset().exclude(status=self._get_deactivated_status())
    
    def create(self, **kwargs: Any) -> Any:
        response = super().create(**kwargs)
        response.clear_cache()
        return response
    
    def delete(self, *args, **kwargs) -> tuple[int, dict[str, int]]:
        response = super().delete(*args, **kwargs)
        self.model.clear_cache()
        return response
    
    def update(self, *args, **kwargs) -> int:
        response = super().update(*args, **kwargs)
        self.model.clear_cache()
        return response

    def bulk_create(self, objs: Iterable[Any], *args, **kwargs) -> list[Any]:
        response = super().bulk_create(objs, *args, **kwargs)
        self.model.clear_cache()
        return response
    
    def bulk_update(self, objs: Iterable[Any], fields: Iterable[str], *args, **kwargs) -> list[Any]:
        response = super().bulk_update(objs, fields, *args, **kwargs)
        self.model.clear_cache()
        return response

    def get_or_create(self, **kwargs: Any) -> tuple[Any, bool]:
        response, created = super().get_or_create(**kwargs)
        if created:
            response.clear_cache()
        return response, created
    
    def update_or_create(self, **kwargs: Any) -> tuple[Any, bool]:
        response = super().update_or_create(**kwargs)
        self.model.clear_cache()
        return response
