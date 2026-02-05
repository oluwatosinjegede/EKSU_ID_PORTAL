from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist

from idcards.models import IDCard
from idcards.generator import generate_id_card as build_id_card
from applications.models import IDApplication

import os
from django.conf import settings


def generate_id_card(application: IDApplication) -> IDCard:
    """
    Create or reuse IDCard for a student and generate image locally.
    Safe for admin + signals + production.
    """

    if not application or not application.student:
        raise ValueError("Invalid application or missing student")

    student = application.student

    with transaction.atomic():
        id_card, created = IDCard.objects.get_or_create(
            student=student,
            defaults={"is_active": True},
        )

        # ----------------------------
        # If image already exists, skip regeneration
        # ----------------------------
        image_field = getattr(id_card, "image", None)

        if image_field and getattr(image_field, "name", None):
            return id_card

        # ----------------------------
        # Generate ID card locally
        # (generator handles saving)
        # ----------------------------
        try:
            build_id_card(id_card)
        except Exception as e:
            raise RuntimeError(f"ID card generation failed: {e}")

        # refresh from DB in case generator updated fields
        id_card.refresh_from_db()

        return id_card

def ensure_id_card_exists(id_card):
    if not id_card or not getattr(id_card, "image", None):
        return

    file_path = os.path.join(settings.MEDIA_ROOT, id_card.image.name)

    if not os.path.exists(file_path):
        build_id_card(id_card)
