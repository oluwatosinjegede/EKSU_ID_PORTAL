from django.db import models
from students.models import Student
import uuid


def idcard_upload_path(instance, filename):
    return f"idcards/{instance.student.matric_no}.png"


def passport_upload_path(instance, filename):
    return f"passports/{instance.student.matric_no}.jpg"


class IDCard(models.Model):
    student = models.OneToOneField(
        Student,
        on_delete=models.CASCADE,
        related_name="id_card",
    )

    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    # Uploaded passport photo
    passport = models.ImageField(upload_to=passport_upload_path, blank=True, null=True)

    # Generated ID card image
    image = models.ImageField(upload_to=idcard_upload_path, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
    student = self.student

    full_name = (
        getattr(student, "full_name", None)
        or f"{getattr(student, 'first_name', '')} {getattr(student, 'last_name', '')}".strip()
        or getattr(student, "name", "")
        or str(student)
    )

    return f"{full_name} ID Card"

