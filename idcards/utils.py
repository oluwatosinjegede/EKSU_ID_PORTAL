from django.db import transaction
from idcards.models import IDCard
from idcards.generator import generate_id_card as build_id_card


def generate_id_card(application):
    """
    Create or reuse IDCard and generate PNG ID image (Cloudinary safe).
    Passport-only workflow. No filesystem. No PDF.
    """

    if not application or not application.student:
        raise ValueError("Invalid application or missing student")

    student = application.student

    with transaction.atomic():

        # Get or create IDCard (avoid duplicates)
        id_card, _ = IDCard.objects.get_or_create(student=student)

        # Copy passport if missing
        if not id_card.passport and application.passport:
            try:
                src_file = application.passport.file
                filename = f"{student.matric_number}_passport.jpg"

                id_card.passport.save(
                    filename,
                    src_file,
                    save=True,
                )
            except Exception:
                pass

        # Skip regeneration if image already exists
        if id_card.image:
            return id_card

        # Generate PNG ID card (Cloudinary)
        build_id_card(id_card)

        id_card.refresh_from_db()
        return id_card
