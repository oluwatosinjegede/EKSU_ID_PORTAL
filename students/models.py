from django.db import models
from django.conf import settings


class Student(models.Model):
    # =========================
    # CORE IDENTITY
    # =========================
    matric_number = models.CharField(
        max_length=30,
        unique=True,
        db_index=True
    )

    first_name = models.CharField(
        max_length=50,
        blank=True,
        default=""
    )

    middle_name = models.CharField(
        max_length=50,
        blank=True,
        default=""
    )

    last_name = models.CharField(
        max_length=50,
        blank=True,
        default=""
    )

    # =========================
    # ACADEMIC
    # =========================
    department = models.CharField(
        max_length=120,
        blank=True,
        default=""
    )

    level = models.CharField(
        max_length=30,
        blank=True,
        default=""
    )

    # =========================
    # CONTACT
    # =========================
    phone = models.CharField(
        max_length=30,
        blank=True,
        default=""
    )

    # =========================
    # USER LINK
    # =========================
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student"
    )

    created_at = models.DateTimeField(auto_now_add=True)



    # =========================
    # SAFE FULL NAME PROPERTY
    # =========================
    @property
    def full_name(self):
        name = " ".join(
            part for part in [
                self.first_name,
                self.middle_name,
                self.last_name
            ] if part
        ).strip()

        return name or self.matric_number

    # =========================
    # STRING REPRESENTATION
    # =========================
    def __str__(self):
        return f"{self.matric_number} - {self.full_name}"
