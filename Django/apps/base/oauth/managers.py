from django.contrib.auth.models import BaseUserManager


class UserManagerWithoutPassword(BaseUserManager):
    """
    Manager for users without password (OAuth)
    """
    def _create_user(self, email, is_staff, is_superuser, **extra_fields):
        if not email:
            raise ValueError("Debe proporcionar el email")
        user = self.model(
            email=self.normalize_email(email),
            is_staff=is_staff,
            is_superuser=is_superuser,
            **extra_fields,
        )
        user.save(using=self.db)
        return user

    def create_user(self, email, **extra_fields):
        return self._create_user(
            email=email,
            is_staff=False,
            is_superuser=False,
            **extra_fields
        )

    def create_superuser(self, email, **extra_fields):

        return self._create_user(
            email=email,
            is_staff=True,
            is_superuser=True,
            **extra_fields
        )