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


class User(AbstractUser):
    
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
    
    def __str__(self) -> str:
        return self.username
    