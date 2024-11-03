from typing import Iterable
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField

from apps.base.cache.base_manager import CacheManager
from apps.base.managers import BaseManager
# Create your models here.

class CacheMixin(models.Model):
    """Mixin made for Models that need to handle Cache features"""
    
    objects = BaseManager()
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs) -> None:
        response = super().save(*args, **kwargs)
        self.clear_cache()
        return response
    
    # Cache Manager properties
    @classmethod
    def get_cache_manager(cls) -> CacheManager:
        return CacheManager(model=cls)
    
    @classmethod
    def clear_cache(cls) -> None:
        """
        Clear the cache pattern for the current model
        for example user-*
        """
        cache_manager = cls.get_cache_manager()
        cache_manager.clear_cache_pattern(pattern=cache_manager.get_model_cache_pattern())
    

class StatusMixin(CacheMixin):
    
    deactivated_status = False
    
    status = models.BooleanField(
        default=True,
        verbose_name=_('Status'),
        help_text=_("Is active✅ / Is not active ❌"),
    )
    def delete(self, *args, **kwargs) -> None:
        self.status = self.deactivated_status
        if hasattr(self, "deleted_date"):
            self.deleted_date = timezone.now().date()
        self.save()
        self.clear_cache()
    
    class Meta:
        abstract = True




class PersonModelMixin(CacheMixin):
    """Mixin made for Models based on persons.
    the Mixin adds the following columns to the model:
    Fields:
    - personal_id (the identification document)
    - personal_email (the personal use email)
    - personal_phone (the personal phone number)
    - gender (The sex of the person)
    - birth_date (The birth date of the person)
    - first_name
    - last_name
    """
    GENDER_MASCULINE = "M"
    GENDER_FEMENINE = "F"
    GENDER_OTHER = "O"
    
    personal_id = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        verbose_name= _("Personal identification"),
        help_text= _("The personal identificator number"),
    ) 
    personal_email = models.EmailField(
        null=True,
        blank=True,
        verbose_name=_("Personal Email"),
        help_text=_("The personal email of this person"),
    )
    personal_phone = PhoneNumberField(
        verbose_name=_("Personal Phone Number"),
        help_text=_("Personal Phone number of this employee"),
        null=True, blank=True,
    )
    
    gender = models.CharField(
        max_length=1,
        choices=(
            (GENDER_MASCULINE, "MASCULINE"),
            (GENDER_FEMENINE, "FEMENINE"),
            (GENDER_OTHER, "OTHER"),
        )
    )
    
    birth_date = models.DateField(
        verbose_name=_("Birth date"),
        help_text=_("The birth date of this person for calculate the age"),
    )
    
    first_name = models.CharField(
        max_length=150,
        verbose_name=_("First name"),
        help_text=_("The First name and Second name if exists"),
    ) 
    
    last_name = models.CharField(
        max_length=150,
        verbose_name=_("Last name"),
        help_text=_("The last name and Second last name if exists"),
    )
    
    home_address = models.TextField(
        verbose_name=_("Home address"),
        help_text=_("The actual residency address of this person"),
        null=True,
        blank=True,
    )
    
    @property
    def age(self) -> int:
        fecha_actual = timezone.now().date()
        age = fecha_actual.year - self.birth_date.year - ((fecha_actual.month, fecha_actual.day) < (self.birth_date.month, self.birth_date.day))
        return age
    
    @property
    def full_name(self) -> str:
        return f'{self.last_name.title()}, {self.first_name.title()}'
    
    @property
    def is_today_birthday(self) -> bool:
        today = timezone.now().date()
        return self.birth_date.day == today.day and self.birth_date.month == today.month
    
    @property
    def days_left_birthday(self) -> int:
        """
        Returns: The days left until the next birthday as integer
        """
        today = timezone.now().date()
        # Próximo cumpleaños este año
        next_birthday = self.birth_date.replace(year=today.year)
        
        # Si el cumpleaños ya pasó este año, calcular el próximo para el siguiente año
        if next_birthday < today:
            next_birthday = self.birth_date.replace(year=today.year + 1)
        
        # Calcular la diferencia en días entre hoy y el próximo cumpleaños
        days_left = (next_birthday - today).days
        return days_left
    
    def __str__(self) -> str:
        return self.full_name
    
    class Meta: 
        abstract = True



class RegisterDatesMixin(CacheMixin):
    created_date = models.DateTimeField(
            auto_now=False,
            auto_now_add=True,
            verbose_name=_("Created date"),
            help_text=_("The date when was created this record"),
        )
    modified_date = models.DateTimeField(
            auto_now=True,
            auto_now_add=False,
            verbose_name=_("Modified date"),
            help_text=_("The date of last modification")
        )
    deleted_date = models.DateTimeField(
            auto_now=False,
            auto_now_add=False,
            null=True,
            blank=True,
            verbose_name=_("Deleted date"),
            help_text=_("The last date when the record was deleted or deactivated")
        )
    
    def delete(self, *args, **kwargs) -> None:
        if hasattr(self, "status") and hasattr(self, "deactivated_status"):
            self.status = self.deactivated_status
        self.deleted_date = timezone.now().date()
        self.save()
        self.clear_cache()
    class Meta:
        abstract = True
        verbose_name = 'RegisterDate'
        verbose_name_plural = 'RegisterDates'

class BaseModel(StatusMixin, RegisterDatesMixin, CacheMixin,):
    """
    Base ABSTRACT model that adds the following features:
    - deactivated_status (specifies what is the data type of Deactivated record)
    - status (the model property which specifies the status of the record (defaults to boolean))
    - created_date (specifies the date when the record was created)
    - modified_date (specifies the date of the last time the record was modified)
    - deleted_date (specifies the last time the record was deactivated)
    - changed_by (Especifica quien fue el ultimo ent ocar el registro) (OBLIGATORIO)
    
    - Save method overrided to clear chache on every save
    - Delete methos overrided to not delete but change status to deleted status (_deactivated_status property)
    
    """
    
    
    changed_by = models.ForeignKey(
            to="users.User",
            on_delete=models.SET_NULL,
            null=True,
            blank=False,
            verbose_name=_("Changed by"),
            help_text=_("The last user that touched this record"),
        )
    
    
    
    # ================================================================
    #       Configuracion del Simple History
    # ================================================================
    #TODO Configuración de la auditoría 
    
    
    # def save(self, *args, **kwargs) -> None:
    #     response = super().save(*args, **kwargs)
    #     self.clear_cache()
    #     return response
    
    def delete(self, *args, **kwargs) -> tuple[int, dict[str, int]]:
        self.status = self.deactivated_status
        self.deleted_date = timezone.now().date()
        self.save()
        self.clear_cache()
    
    class Meta: 
        abstract = True
        verbose_name = _("Base model")
        verbose_name_plural = _("Base models")

