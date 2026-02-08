from django.db import models
from django.utils import timezone
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
    # RELATION (ONE APPLICATION PER STUDENT)
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
        blank=True,
        null=True,
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

    reviewed_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    rejection_reason = models.TextField(
        blank=True,
        default="",
    )

    # =====================================================
    # TIMESTAMP
    # =====================================================
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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

    @property
    def has_passport(self):
        return bool(self.passport)

    # =====================================================
    # STATE TRANSITION HELPERS
    # =====================================================
    def approve(self, reviewer_username=""):
        """Safely approve application."""
        self.status = self.STATUS_APPROVED
        self.reviewed_by = reviewer_username
        self.reviewed_at = timezone.now()
        self.save(update_fields=["status", "reviewed_by", "reviewed_at"])

    def reject(self, reviewer_username="", reason=""):
        """Safely reject application."""
        self.status = self.STATUS_REJECTED
        self.reviewed_by = reviewer_username
        self.reviewed_at = timezone.now()
        self.rejection_reason = reason
        self.save(
            update_fields=[
                "status",
                "reviewed_by",
                "reviewed_at",
                "rejection_reason",
            ]
        )

    # =====================================================
    # STRING
    # =====================================================
    def __str__(self):
        return f"ID Application - {self.student}"
