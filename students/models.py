from django.db import models
from django.conf import settings


class Student(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    matric_number = models.CharField(max_length=40, unique=True)
    department = models.CharField(max_length=100)
    phone = models.CharField(max_length=25)

    level = models.CharField(
        max_length=20,
        choices=[
            ("100", "100 Level"),
            ("200", "200 Level"),
            ("300", "300 Level"),
            ("400", "400 Level"),
            ("500", "500 Level"),
        ],
        default="100",
    )

    middle_name = models.CharField(
        max_length=50,
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.matric_number
