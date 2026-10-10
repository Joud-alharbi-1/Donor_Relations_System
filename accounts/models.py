from django.db import models
from django.contrib.auth.models import AbstractUser
from entities.models import Donor, Beneficiary

# Create your models here.

class Role(models.Model):
    ADMIN = 'manager'
    DONOR = 'donor'
    BENEFICIARY = 'beneficiary'

    ROLE_CHOICES = [
        (ADMIN, 'Manager'),
        (DONOR, 'Donor'),
        (BENEFICIARY, 'Beneficiary'),
    ]

    name = models.CharField(max_length=20, choices=ROLE_CHOICES, unique=True)

    def __str__(self):
        return self.name


class User(AbstractUser):
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name='users')
    phone = models.CharField(max_length=20, blank=True, null=True)

    # يحدد أي جهة مانحة يمثّلها الحساب — فارغ لغير المانح (الإدارة، المستفيد)
    donor = models.OneToOneField(
        Donor, on_delete=models.SET_NULL, blank=True, null=True, related_name='user'
    )
    # يحدد أي جهة مستفيدة يمثّلها الحساب — فارغ لغير المستفيد
    beneficiary = models.OneToOneField(
        Beneficiary, on_delete=models.SET_NULL, blank=True, null=True, related_name='user'
    )

    def __str__(self):
        return self.username