from datetime import datetime as dt
from django.db import models
# from simple_history.models import HistoricalRecords
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache
from apps.base.constants import sex_choices, nature_choices

# Create your models here.
SEX_CHOICES = (
    (sex_choices.MALE, 'MASCULINO'),
    (sex_choices.FEMALE, 'FEMENINO'),
)
NATURE_CHOICES = (
    (nature_choices.VENEZOLANO, "VENEZOLANO"),
    (nature_choices.JURIDICO, "JURIDICO"),
    (nature_choices.EXTRANJERO, "EXTRANJERO"),
)

class PersonModelMixin(models.Model): # hay que heredarle el model igual para que funcione xd
    """Mixin made for Models based on persons.
    the Mixin adds the following columns to the model:
    - nature (J, V, E)
    - identification (the identification document)
    - personal_email (the personal use email)
    - sex (The sex of the person)
    - first_name
    - last_name
    
    """
    nature = models.CharField(
            max_length=1,
            verbose_name=_("Identification Nature"),
            choices=NATURE_CHOICES,
            default=nature_choices.VENEZOLANO
        )
    identification = models.CharField(
            max_length=15,
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
    
    sex = models.CharField(
        max_length=1,
        choices=SEX_CHOICES,
        default=sex_choices.MALE,
    )
    
    birth_date = models.DateField(
        verbose_name=_("Birth date"),
    )
    
    first_name = models.CharField(
        max_length=120,
        verbose_name=_("First name"),
    ) 
    
    last_name = models.CharField(
        max_length=120,
        verbose_name=_("Last name"),
    )
    
    home_address = models.TextField(
        verbose_name=_("Home address"),
        null=True,
        blank=True,
    )
    
    def __str__(self) -> str:
        return f'{self.last_name}, {self.first_name}'
    
    class Meta: 
        abstract = True


class BaseModel(models.Model):
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
    
    deactivated_status = False
    
    
    status = models.BooleanField(
            default=True,
            verbose_name=_('Status'),
            help_text=_("Is active✅ / Is not active ❌"),
        )
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
    changed_by = models.BigIntegerField(
            # null=False,
            # blank=False,
            verbose_name=_("Changed by"),
            help_text=_("The last user that touched this record"),
        )
    #TODO Configuración de la auditoría 
    
    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)
        # cache.clear() #? Limpia todo el cache
    
    def delete(self, *args, **kwargs) -> tuple[int, dict[str, int]]:
        self.status = self.deactivated_status
        self.deleted_date = dt.now(tz=None)
        self.save()
    
    class Meta: 
        abstract = True
        verbose_name = _("Base model")
        verbose_name_plural = _("Base models")

