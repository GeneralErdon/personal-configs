from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager
from django.utils.translation import gettext_lazy as _
# Create your models here.

def user_media(instance:AbstractUser, filename: str) -> str:
    
    return "users/{username}/{filename}" \
                .format(
                    username=instance.username,
                    filename=filename,
                    )


MEDIC_ROLE = "M"
NURSE_ROLE = "E"
ADMINISTRATIVE_ROLE = "A"

class User(AbstractUser):
    
    USER_ROLES = (
        ("M", _("Medic")),
        ("E", _("Nurse")),
        ("A", _("Administrative")),
    )
    
    birth_date = models.DateField(
        verbose_name=_("Birth Date"),
        help_text=_("This is your birth date"),
        null=True, blank=True
        )
    photo = models.ImageField(
        verbose_name=_("Photo"),
        help_text=_("User's Photo"),
        null=True,
        blank=True,
        upload_to=user_media,
        )
    
    # role = models.CharField(
    #     verbose_name=_("Role"),
    #     db_index=True,
    #     help_text=_("User role"),
    #     max_length=1,
    #     choices=USER_ROLES,
    #     default=ADMINISTRATIVE_ROLE,
    # )
    
    
    def __str__(self) -> str:
        return self.username
    