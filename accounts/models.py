from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('STUDENT', 'Student'),
        ('REVIEWER', 'Reviewer'),
        ('APPROVER', 'Approver'),
        ('ADMIN', 'Administrator'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='STUDENT')
    must_change_password = models.BooleanField(default=True)

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='STUDENT'
    )

    must_change_password = models.BooleanField(default=True)

    # FIX reverse accessor clashes
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='accounts_user_set',
        blank=True,
    )

    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='accounts_user_permissions_set',
        blank=True,
    )

    @property
    def can_access_admin(self):
        return self.role in ['REVIEWER', 'APPROVER', 'ADMIN']
