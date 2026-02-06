from django.db import models
from students.models import Student
from cloudinary.models import CloudinaryField


class IDApplication(models.Model):
    # =====================================================
    # STATUS
    # =====================================================
    STATUS_PENDING = "PENDING"
    STATUS_APPROVED = "APPROVED"
    STATUS_REJECTED = "REJECTED"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    ]

    # =====================================================
    # RELATION
    # =====================================================
    student = models.OneToOneField(
        Student,
        on_delete=models.CASCADE,
        related_name="id_application",
        db_index=True,
    )

    # =====================================================
    # PASSPORT (Cloudinary)
    # =====================================================
    passport = CloudinaryField(
        "passport",
        resource_type="image",
        folder="id_applications/passports",
    )

    # =====================================================
    # REVIEW STATUS
    # =====================================================
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
    )

    reviewed_by = models.CharField(
        max_length=150,
        blank=True,
        default="",
    )

    # =====================================================
    # TIMESTAMP
    # =====================================================
    created_at = models.DateTimeField(auto_now_add=True)

    # =====================================================
    # HELPERS
    # =====================================================
    @property
    def is_pending(self):
        return self.status == self.STATUS_PENDING

    @property
    def is_approved(self):
        return self.status == self.STATUS_APPROVED

    @property
    def is_rejected(self):
        return self.status == self.STATUS_REJECTED

    # =====================================================
    # STRING
    # =====================================================
    def __str__(self):
        return f"ID Application - {self.student}"
