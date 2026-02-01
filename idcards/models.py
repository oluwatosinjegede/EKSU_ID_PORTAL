from django.db import models
from django.utils import timezone
import uuid


class IDCard(models.Model):
    # ✅ Secure public identifier (used for QR verification)
    uid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
    )

    student = models.OneToOneField(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="id_card",
    )

    pdf = models.FileField(
        upload_to="idcards/",
        blank=True,
        null=True,
    )

    issued_at = models.DateTimeField(
        default=timezone.now,
        editable=False,
    )

    def __str__(self):
        return f"ID Card - {self.student.matric_number}"
