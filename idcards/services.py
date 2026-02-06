from django.db import transaction
from django.conf import settings
from django.core.files.base import ContentFile
import os
import requests

from idcards.models import IDCard
from idcards.generator import generate_id_card as build_id_card
from applications.models import IDApplication


def generate_id_card(application: IDApplication) -> IDCard:
    """
    Create or reuse IDCard and generate image locally.
    Cloudinary -> local safe conversion included.
    """

    if not application or not application.student:
        raise ValueError("Invalid application or missing student")

    student = application.student

    with transaction.atomic():

        # -------------------------------------------------
        # Create or fetch IDCard
        # -------------------------------------------------
        id_card, _ = IDCard.objects.get_or_create(student=student)

        # -------------------------------------------------
        # Copy passport from Application -> IDCard safely
        # (Supports Cloudinary OR local file)
        # -------------------------------------------------
        if not id_card.passport and getattr(application, "passport", None):

            src = application.passport

            try:
                # ---------- Remote storage (Cloudinary / S3 / URL) ----------
                if hasattr(src, "url") and src.url:
                    response = requests.get(src.url, timeout=15, stream=True)
                    if response.status_code == 200:
                        filename = f"{student.matric_no}_passport.jpg"
                        id_card.passport.save(
                            filename,
                            ContentFile(response.content),
                            save=False,
                        )

                # ---------- Local file ----------
                elif hasattr(src, "path") and os.path.exists(src.path):
                    with open(src.path, "rb") as f:
                        filename = os.path.basename(src.name)
                        id_card.passport.save(
                            filename,
                            ContentFile(f.read()),
                            save=False,
                        )

                if id_card.passport:
                    id_card.save(update_fields=["passport"])

            except Exception:
                # Never crash generation due to passport issue
                pass

        # -------------------------------------------------
        # If image exists in DB ? ensure physical file exists
        # (Railway ephemeral disk protection)
        # -------------------------------------------------
        if id_card.image and id_card.image.name:
            ensure_id_card_exists(id_card)
            return id_card

        # -------------------------------------------------
        # Generate ID card image
        # -------------------------------------------------
        try:
            build_id_card(id_card)
        except Exception as e:
            raise RuntimeError(f"ID card generation failed: {e}")

        id_card.refresh_from_db()
        return id_card


def ensure_id_card_exists(id_card: IDCard):
    """
    Rebuild image if DB has path but file missing (Railway disk reset fix)
    """

    if not id_card or not id_card.image or not id_card.image.name:
        return

    file_path = os.path.join(settings.MEDIA_ROOT, id_card.image.name)

    # If missing ? regenerate safely (no recursion)
    if not os.path.exists(file_path):
        try:
            build_id_card(id_card)
        except Exception:
            pass
