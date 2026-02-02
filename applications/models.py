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

    student = models.OneToOneField(
        Student,
        on_delete=models.CASCADE,
        related_name="id_application",
    )

    passport = CloudinaryField(
        "passport",
        resource_type="image",
        folder="id_applications/passports",
    )

    signature = CloudinaryField(
        "signature",
        resource_type="image",
        folder="id_applications/signatures",
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )

    reviewed_by = models.CharField(max_length=150, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ID Application – {self.student}"
