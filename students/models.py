from django.db import models
from django.conf import settings


class Student(models.Model):
    # =========================
    # CORE IDENTITY
    # =========================
    matric_number = models.CharField(
        max_length=50,          # Increased (prevents truncation errors)
        unique=True,
        db_index=True,
    )

    first_name = models.CharField(
        max_length=100,         # Increased for long names
        blank=True,
        default="",
    )

    middle_name = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )

    last_name = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )

    # =========================
    # ACADEMIC
    # =========================
    department = models.CharField(
        max_length=150,         # Increased (e.g. PUBLIC ADMINISTRATION)
        blank=True,
        default="",
    )

    level = models.CharField(
        max_length=50,
        blank=True,
        default="",
    )

    # =========================
    # CONTACT
    # =========================
    phone = models.CharField(
        max_length=30,
        blank=True,
        default="",
    )

    # =========================
    # USER LINK
    # =========================
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student",
    )

    # Safe for existing rows during migration
    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True,
    )

    # =========================
    # SAFE FULL NAME PROPERTY
    # =========================
    @property
    def full_name(self):
        parts = [self.first_name, self.middle_name, self.last_name]
        name = " ".join(p for p in parts if p).strip()
        return name if name else self.matric_number

    # =========================
    # STRING REPRESENTATION
    # =========================
    def __str__(self):
        return f"{self.matric_number} - {self.full_name}"
