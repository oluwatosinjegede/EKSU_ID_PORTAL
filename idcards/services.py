from .models import IDCard
from .qr import generate_qr_code
from .pdf import generate_id_card_pdf


def generate_id_card(application):
    student = application.student

    # Create ID card record
    id_card = IDCard.objects.create(
        student=student,
    )

    # Generate QR
    generate_qr_code(id_card)

    # Generate & upload PDF (Cloudinary handled inside)
    generate_id_card_pdf(id_card)

    # ✅ NOTHING else to do here
    # ❌ Do NOT touch id_card.pdf.name
    # ❌ Do NOT use MEDIA_ROOT
    # ❌ Do NOT compute paths

    return id_card
