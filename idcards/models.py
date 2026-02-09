from django.db import models
from students.models import Student
from cloudinary.models import CloudinaryField
import uuid
import secrets


# =====================================================
# LEGACY MIGRATION COMPATIBILITY (DO NOT REMOVE YET)
# =====================================================
def idcard_upload_path(instance, filename):
    matric = getattr(instance.student, "matric_no", None) or instance.uid
    return f"idcards/{matric}.png"


def passport_upload_path(instance, filename):
    matric = getattr(instance.student, "matric_no", None) or instance.uid
    return f"passports/{matric}.jpg"


# =====================================================
# MODEL
# =====================================================
class IDCard(models.Model):

    # =================================================
    # CORE IDENTITY
    # =================================================
    student = models.OneToOneField(
        Student,
        on_delete=models.CASCADE,
        related_name="id_card",
    )

    uid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    # =================================================
    # CLOUDINARY STORAGE
    # =================================================
    passport = CloudinaryField(
        "image",
        folder="passports",
        blank=True,
        null=True,
    )

    image = CloudinaryField(
        "image",
        folder="idcards",
        blank=True,
        null=True,
    )

    # =================================================
    # SECURITY — QR VERIFICATION
    # =================================================
    verify_token = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        db_index=True,
        help_text="Secure token embedded in QR to prevent forgery",
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Disable to invalidate card without deleting",
    )

    is_revoked = models.BooleanField(
        default=False,
        help_text="Revoked cards cannot be verified",
    )

    revoked_reason = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    # =================================================
    # PERFORMANCE INDEXES
    # =================================================
    class Meta:
        indexes = [
            models.Index(fields=["uid"]),
            models.Index(fields=["verify_token"]),
            models.Index(fields=["created_at"]),
        ]

    # =================================================
    # TOKEN GENERATOR
    # =================================================
    def generate_token(self, save=True):
        """
        Generates cryptographically secure QR verification token.
        """
        self.verify_token = secrets.token_urlsafe(32)
        if save:
            self.save(update_fields=["verify_token"])

    # =================================================
    # STATUS HELPERS
    # =================================================
    @property
    def has_image(self):
        return bool(self.image and getattr(self.image, "public_id", None))

    @property
    def has_passport(self):
        return bool(self.passport and getattr(self.passport, "public_id", None))

    @property
    def is_valid(self):
        """
        True only if card is active and not revoked.
        """
        return self.is_active and not self.is_revoked

    # =================================================
    # NAME BUILDER (SAFE)
    # =================================================
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

    # =================================================
    # REVOKE / RESTORE
    # =================================================
    def revoke(self, reason="Card revoked"):
        self.is_revoked = True
        self.revoked_reason = reason
        self.save(update_fields=["is_revoked", "revoked_reason"])

    def restore(self):
        self.is_revoked = False
        self.revoked_reason = None
        self.save(update_fields=["is_revoked", "revoked_reason"])

    # =================================================
    # STRING
    # =================================================
    def __str__(self):
        return f"{self.get_full_name()} ID Card"
