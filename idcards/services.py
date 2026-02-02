from django.core.files import File
from django.db import transaction

from .models import IDCard
from .qr import generate_qr_code
from .pdf import generate_id_card_pdf


def generate_id_card(application):
    """
    Generate ID card PDF and upload to Cloudinary (RAW).
    Safe to call multiple times.
    """

    student = application.student

    with transaction.atomic():
        id_card, created = IDCard.objects.get_or_create(
            student=student,
            defaults={"is_active": True},
        )

        # If PDF already exists, do nothing
        if id_card.pdf:
            return id_card

        # Generate QR code (should update IDCard)
        generate_qr_code(id_card)

        # Generate PDF locally
        pdf_path = generate_id_card_pdf(id_card)

        # Upload PDF to Cloudinary via Django storage
        with open(pdf_path, "rb") as f:
            id_card.pdf.save(
                pdf_path.name,
                File(f),
                save=True,
            )

    return id_card
