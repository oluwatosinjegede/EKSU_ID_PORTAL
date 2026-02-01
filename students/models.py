from django.db import models
from django.conf import settings


class Student(models.Model):
    matric_number = models.CharField(max_length=30, unique=True)
    middle_name = models.CharField(
    max_length=30,
    blank=True,
    null=True
)

    department = models.CharField(max_length=100)
    level = models.CharField(max_length=10)
    phone = models.CharField(max_length=30, blank=True)

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.matric_number
