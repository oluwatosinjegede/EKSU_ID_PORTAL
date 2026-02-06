from django.db import models
from students.models import Student
from cloudinary.models import CloudinaryField


class IDApplication(models.Model):
    STATUS_PENDING = "PENDING"
    STATUS_APPROVED = "APPROVED"
    STATUS_REJECTED = "REJECTED"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    ]

    # =========================
    # STUDENT LINK
    # =========================
    student = models.OneToOneField(
        Student,
        on_delete=models.CASCADE,
        related_name="id_application",
    )

    # =========================
    # PASSPORT PHOTO (ONLY IMAGE REQUIRED)
    # =========================
    passport = CloudinaryField(
        "passport",
        resource_type="image",
        folder="id_applications/passports",
        blank=False,     # passport REQUIRED
        null=False,
    )

    # =========================
    # APPLICATION STATUS
    # =========================
    status = models.CharField(
        max_length=10,
