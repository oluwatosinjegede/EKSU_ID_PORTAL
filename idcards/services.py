from django.db import transaction
from django.conf import settings
import os

from idcards.models import IDCard
from idcards.generator import generate_id_card as build_id_card
from applications.models import IDApplication


def generate_id_card(application: IDApplication) -> IDCard:
    """
    Create or reuse IDCard for a student and generate image locally.
    Safe for admin + signals + production.
    """

    if not application or not application.student:
        raise ValueError("Invalid application or missing student")

    student = application.student

    with transaction.atomic():
        # ? removed is_active (field does not exist anymore)
        id_card, created = IDCard.objects.get_or_create(
            student=student
        )

        # ----------------------------
        # If image already exists in DB, ensure file exists on disk
        # ----------------------------
        if id_card.image and id_card.image.name:
            ensure_id_card_exists(id_card)
            return id_card

        # ----------------------------
        # Generate ID card locally
        # ----------------------------
        try:
            build_id_card(id_card)
        except Exception as e:
            raise RuntimeError(f"ID card generation failed: {e}")

        id_card.refresh_from_db()
        return id_card


def ensure_id_card_exists(id_card: IDCard):
    """
    Rebuild image if DB has path but file missing (Railway ephemeral disk fix)
    """

    if not id_card or not id_card.image:
        return

    file_path = os.path.join(settings.MEDIA_ROOT, id_card.image.name)

    if not os.path.exists(file_path):
        try:
            build_id_card(id_card)
        except Exception:
            pass
