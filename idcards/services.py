from django.db import transaction
from idcards.models import IDCard
from idcards.qr import generate_qr_code
from idcards.pdf import generate_id_card_pdf


def generate_id_card(application):
    """
    Create an IDCard and generate its QR code + PDF.
    Safe to call multiple times (idempotent).
    """

    student = application.student

    with transaction.atomic():
        # Create ID card once per student
        id_card, created = IDCard.objects.get_or_create(
            student=student,
            defaults={"is_active": True},
        )

        # If PDF already exists, do nothing
        if id_card.pdf:
            return id_card

        # Generate QR (should only depend on id_card.uid)
        generate_qr_code(id_card)

        # Generate PDF and upload to Cloudinary (RAW)
        result = generate_id_card_pdf(id_card)

        # Assign Cloudinary public_id to CloudinaryField
        id_card.pdf = result["public_id"]
        id_card.save(update_fields=["pdf"])

    return id_card
