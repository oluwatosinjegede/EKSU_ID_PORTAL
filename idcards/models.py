from django.db import models
from students.models import Student
from cloudinary.models import CloudinaryField
import uuid


class IDCard(models.Model):
    student = models.OneToOneField(
        Student,
        on_delete=models.CASCADE,
        related_name="id_card",
    )

    # Public unique identifier (QR / verification)
    uid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True,
    )

    # PDF stored in Cloudinary (RAW)
    pdf = CloudinaryField(
        resource_type="raw",
        folder="idcards/pdfs",
        blank=True,
        null=True,
    )

    is_active = models.BooleanField(default=True)
    issued_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ID Card - {self.student}"
