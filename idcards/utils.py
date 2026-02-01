from django.template.loader import get_template
from xhtml2pdf import pisa
from django.conf import settings
from .models import IDCard
from .qr import generate_qr_code
import os

def generate_id_card(application):
    student = application.student

    id_card = IDCard.objects.create(student=student)

    qr_url = generate_qr_code(id_card.uid)

    template = get_template('idcard.html')
    html = template.render({
        'student': student,
        'passport': application.passport.url,
        'signature': application.signature.url,
        'qr_code': qr_url,
        'uid': id_card.uid,
    })

    output_path = os.path.join(
        settings.MEDIA_ROOT,
        f"idcards/{student.matric_number}.pdf"
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "wb") as file:
        pisa.CreatePDF(html, dest=file)

    id_card.pdf.name = f"idcards/{student.matric_number}.pdf"
    id_card.save()

    return id_card
