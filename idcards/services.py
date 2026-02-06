from django.db import transaction
from django.core.files.base import ContentFile

from idcards.models import IDCard
from idcards.generator import generate_id_card as build_id_card
from applications.models import IDApplication


def generate_id_card(application: IDApplication) -> IDCard:
    """
    Create or reuse IDCard and generate Cloudinary image safely.
    No filesystem dependency. Production-safe.
    """

    if not application or not application.student:
        raise ValueError("Invalid application or missing student")

    student = application.student

    with transaction.atomic():

        # -------------------------------------------------
        # Get or create IDCard
        # -------------------------------------------------
        id_card, _ = IDCard.objects.get_or_create(student=student)

        # -------------------------------------------------
        # Copy passport from Application -> IDCard (Cloudinary-safe)
        # -------------------------------------------------
        if not id_card.passport and getattr(application, "passport", None):
            try:
                # Directly copy file via Django storage (no HTTP download)
                src_file = application.passport.file
                filename = f"{student.matric_number}_passport.jpg"

                id_card.passport.save(
                    filename,
                    ContentFile(src_file.read()),
                    save=False,
                )
                id_card.save(update_fields=["passport"])

            except Exception:
                # Never crash if passport copy fails
                pass

        # -------------------------------------------------
        # If image already exists ? reuse (skip regeneration)
        # -------------------------------------------------
        if id_card.image:
            return id_card

        # -------------------------------------------------
        # Generate ID image (Cloudinary backend handles storage)
        # -------------------------------------------------
        try:
            build_id_card(id_card)
        except Exception as e:
            raise RuntimeError(f"ID card generation failed: {e}")

        id_card.refresh_from_db()
        return id_card


# -------------------------------------------------
# Compatibility helper (kept for old calls)
# -------------------------------------------------
def ensure_id_card_exists(id_card: IDCard):
    """
    Rebuild ID image if missing (Cloudinary-safe).
    No filesystem check needed.
    """

    if not id_card:
        return

    if not id_card.image:
        try:
            build_id_card(id_card)
        except Exception:
            pass
