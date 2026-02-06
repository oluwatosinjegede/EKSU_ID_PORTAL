from django.db import models
from students.models import Student
import uuid


# =========================
# SAFE PATH BUILDERS
# =========================
def idcard_upload_path(instance, filename):
    matric = getattr(instance.student, "matric_no", None) or instance.uid
    return f"idcards/{matric}.png"


def passport_upload_path(instance, filename):
    matric = getattr(instance.student, "matric_no", None) or instance.uid
    return f"passports/{matric}.jpg"


# =========================
# MODEL
# =========================
class IDCard(models.Model):
    student = models.OneToOneField(
        Student,
        on_delete=models.CASCADE,
        related_name="id_card",
    )

    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    # Uploaded passport photo
    passport = CloudinaryField(
        upload_to=passport_upload_path,
        blank=True,
        null=True,
    )

    # Generated ID card image
    image = CloudinaryField(
        upload_to=idcard_upload_path,
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    image = CloudinaryField("image", blank=True, null=True)

    # =========================
    # SAFE NAME BUILDER
    # =========================
    def get_full_name(self):
        student = self.student

        first = getattr(student, "first_name", "") or ""
        middle = getattr(student, "middle_name", "") or ""
        last = getattr(student, "last_name", "") or ""

        full_name = " ".join(filter(None, [first, middle, last])).strip()

        if not full_name:
            full_name = getattr(student, "full_name", None) \
                        or getattr(student, "name", None) \
                        or str(student)

        return full_name

    # =========================
    # STRING REPRESENTATION
    # =========================
    def __str__(self):
        return f"{self.get_full_name()} ID Card"
