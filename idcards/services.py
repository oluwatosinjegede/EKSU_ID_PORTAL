from django.conf import settings
from .models import IDCard
from .qr import generate_qr_code
from .pdf import generate_id_card_pdf


def generate_id_card(application):
    student = application.student

    # Create ID card record
    id_card = IDCard.objects.create(
        student=student,
        is_active=True,
    )

    # Generate QR
    generate_qr_code(id_card)

    # Generate PDF
    pdf_path = generate_id_card_pdf(id_card)

    # Persist PDF path
    id_card.pdf.name = pdf_path.relative_to(settings.MEDIA_ROOT).as_posix()
    id_card.save(update_fields=["pdf"])

    return id_card
