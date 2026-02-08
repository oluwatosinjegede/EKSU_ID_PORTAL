from django.db import models
from students.models import Student
from cloudinary.models import CloudinaryField
import uuid


# =====================================================
# TEMPORARY MIGRATION COMPATIBILITY FIX (OPTION A)
# Required by old migrations — DO NOT REMOVE YET
# =====================================================
def idcard_upload_path(instance, filename):
    """
    Legacy function required by old migrations.
    Safe to keep. Harmless if unused.
    """
    matric = getattr(instance.student, "matric_no", None) or instance.uid
    return f"idcards/{matric}.png"


def passport_upload_path(instance, filename):
    """
    Legacy function required by old migrations.
    Safe to keep. Harmless if unused.
    """
    matric = getattr(instance.student, "matric_no", None) or instance.uid
    return f"passports/{matric}.jpg"


# =====================================================
# MODEL
# =====================================================
class IDCard(models.Model):
    student = models.OneToOneField(
        Student,
        on_delete=models.CASCADE,
        related_name="id_card",
    )

    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    # -------------------------------------------------
    # Passport Photo (Uploaded by student)
    # -------------------------------------------------
    passport = CloudinaryField(
        "image",
        folder="passports",
        blank=True,
        null=True,
    )

    # -------------------------------------------------
    # Generated ID Card Image
    # -------------------------------------------------
    image = CloudinaryField(
        "image",
        folder="idcards",
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["uid"]),
            models.Index(fields=["created_at"]),
        ]

    # -------------------------------------------------
    # Safe full name builder
    # -------------------------------------------------
    def get_full_name(self):
        student = self.student

        first = getattr(student, "first_name", "") or ""
        middle = getattr(student, "middle_name", "") or ""
        last = getattr(student, "last_name", "") or ""

        name = " ".join(filter(None, [first, middle, last])).strip()

        if not name:
            name = (
                getattr(student, "full_name", None)
                or getattr(student, "name", None)
                or str(student)
            )

        return name

    # -------------------------------------------------
    # Status helpers
    # -------------------------------------------------
    @property
    def has_image(self):
        return bool(self.image and getattr(self.image, "public_id", None))

    @property
    def has_passport(self):
        return bool(self.passport and getattr(self.passport, "public_id", None))

    # -------------------------------------------------
    # String representation
    # -------------------------------------------------
    def __str__(self):
        return f"{self.get_full_name()} ID Card"
