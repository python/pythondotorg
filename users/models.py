from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class UserManager(UserManager):
    def create_superuser(self, username, password, email=None, **extra_fields):
        u = self.create_user(username, email, password, **extra_fields)
        u.is_staff = True
        u.is_active = True
        u.is_superuser = True
        u.save(using=self._db)
        return u


class User(AbstractUser):
    is_beta_tester = models.BooleanField(default=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'
