from django.db import transaction
from django.core.files.base import ContentFile

from idcards.models import IDCard
from idcards.generator import generate_id_card as build_id_card
from applications.models import IDApplication


# =====================================================
# MAIN SERVICE — CREATE / GENERATE ID SAFELY
# =====================================================
def generate_id_card(application: IDApplication) -> IDCard:
    """
    Create or reuse IDCard and generate image safely.
    Fully idempotent, Cloudinary-safe, race-condition safe.
    """

    if not application or not application.student:
        raise ValueError("Invalid application or missing student")

    if application.status != IDApplication.STATUS_APPROVED:
        raise ValueError("Cannot generate ID: application not approved")

    if not application.passport:
        raise ValueError("Cannot generate ID: passport missing")

    student = application.student

    with transaction.atomic():

        # -------------------------------------------------
        # Get or create IDCard
        # -------------------------------------------------
        id_card, _ = IDCard.objects.get_or_create(student=student)

        # -------------------------------------------------
        # Ensure passport exists on IDCard
        # -------------------------------------------------
        if not id_card.passport and application.passport:
            try:
                src = application.passport.file
                src.seek(0)

                filename = f"{student.matric_number or id_card.uid}_passport.jpg"

                id_card.passport.save(
                    filename,
                    ContentFile(src.read()),
                    save=False,
                )
                id_card.save(update_fields=["passport"])

            except Exception:
                # Do not crash if Cloudinary copy fails
                pass

        # -------------------------------------------------
        # If image already exists ? return (idempotent)
        # -------------------------------------------------
        if id_card.image and getattr(id_card.image, "name", None):
            return id_card

        # -------------------------------------------------
        # Generate ID image
        # -------------------------------------------------
        try:
            build_id_card(id_card)
        except Exception as e:
            raise RuntimeError(f"ID generation failed: {e}")

        id_card.refresh_from_db()
        return id_card


# =====================================================
# SAFE ENSURE (REBUILD IF MISSING)
# =====================================================
def ensure_id_card_exists(id_card: IDCard):
    """
    Ensure ID image exists. Rebuild if missing.
    Safe for admin, signals, background jobs.
    """

    if not id_card:
        return None

    if id_card.image and getattr(id_card.image, "name", None):
        return id_card.image.url

    # Must have approved application
    application = IDApplication.objects.filter(
        student=id_card.student,
        status=IDApplication.STATUS_APPROVED,
    ).first()

    if not application or not application.passport:
        return None

    try:
        build_id_card(id_card)
        id_card.refresh_from_db()
    except Exception:
        return None

    return getattr(id_card.image, "url", None)
