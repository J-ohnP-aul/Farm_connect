"""Custom user model — database-design.md §5.1.

Phone number is the username (my call §4.3: password auth in V1, OTP as a
V2 layer). Buyers never get rows (BR-03): registration is farmer-only.
"""

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create(self, phone_number, password, **extra_fields):
        if not phone_number:
            raise ValueError('Phone number is required')
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create(phone_number, password, **extra_fields)

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', self.model.Role.ADMIN)
        return self._create(phone_number, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        FARMER = 'farmer', 'Farmer'
        ADMIN = 'admin', 'Administrator'

    # phone number replaces username (database-design.md §5.1)
    phone_number = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=120, blank=True)
    role = models.CharField(
        max_length=10, choices=Role.choices, default=Role.FARMER,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['name']  # used by createsuperuser only

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    def __str__(self):
        return f'{self.name} ({self.phone_number})'

    @property
    def is_farmer(self):
        return self.role == self.Role.FARMER
