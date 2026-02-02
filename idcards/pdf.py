from io import BytesIO
import requests
import cloudinary.uploader

from django.conf import settings
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.lib.utils import ImageReader


# ================= CARD SIZE (ISO ID-1) =================
CARD_WIDTH, CARD_HEIGHT = (85.60 * mm, 53.98 * mm)

# ================= COLORS =================
EKSU_BLUE = HexColor("#8B0000")
DARK = HexColor("#0f172a")
LIGHT_BG = HexColor("#f8fafc")
GRAY = HexColor("#64748b")


def get_student_full_name(student):
    parts = [
        student.user.first_name,
        student.middle_name,
        student.user.last_name,
    ]
    return " ".join(p for p in parts if p)


def image_from_url(url, timeout=10):
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return ImageReader(BytesIO(response.content))


def generate_id_card_pdf(id_card) -> dict:
    """
    Generates ID card PDF in memory and uploads to Cloudinary (RAW).
    RETURNS: Cloudinary upload result dict.
    """

    student = id_card.student
    application = getattr(student, "idapplication", None)

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(CARD_WIDTH, CARD_HEIGHT))

    # ================= BACKGROUND =================
    c.setFillColor(LIGHT_BG)
    c.rect(0, 0, CARD_WIDTH, CARD_HEIGHT, fill=1)

    # ================= LEFT ACCENT =================
    c.setFillColor(EKSU_BLUE)
    c.rect(0, 0, 4, CARD_HEIGHT, fill=1)

    # ================= HEADER =================
    c.setFillColor(EKSU_BLUE)
    c.rect(0, CARD_HEIGHT - 16, CARD_WIDTH, 16, fill=1)

    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(
        CARD_WIDTH / 2,
        CARD_HEIGHT - 11,
        "EKITI STATE UNIVERSITY (EKSU)",
    )

    # ================= QR CODE =================
    BASE_URL = settings.SITE_URL
    verify_url = f"{BASE_URL}/verify/{id_card.uid}/"

    qr_widget = qr.QrCodeWidget(verify_url)
    bounds = qr_widget.getBounds()
    qr_size = 22 * mm

    qr_drawing = Drawing(
        qr_size,
        qr_size,
        transform=[
            qr_size / (bounds[2] - bounds[0]),
            0,
            0,
            qr_size / (bounds[3] - bounds[1]),
            0,
            0,
        ],
    )
    qr_drawing.add(qr_widget)

    qr_x, qr_y = 10, 8
    c.roundRect(qr_x - 2, qr_y - 2, qr_size + 4, qr_size + 4, 4, fill=1, stroke=0)
    qr_drawing.drawOn(c, qr_x, qr_y)

    # ================= PASSPORT PHOTO =================
    photo_size = qr_size
    photo_x = CARD_WIDTH - photo_size - 8
    photo_y = 8

    if application and application.passport:
        try:
            passport_img = image_from_url(application.passport.url)
            c.drawImage(
                passport_img,
                photo_x,
                photo_y,
                photo_size,
                photo_size,
                preserveAspectRatio=True,
                mask="auto",
            )
        except Exception as e:
            print(f"Passport load failed: {e}")

    # ================= STUDENT DETAILS =================
    center_left = qr_x + qr_size + 8
    center_right = photo_x - 8
    center_x = (center_left + center_right) / 2

    start_y = CARD_HEIGHT - 46
    gap = 9

    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 10.5)
    c.drawCentredString(center_x, start_y, get_student_full_name(student).upper())

    c.setFont("Helvetica", 8.5)
    c.setFillColor(GRAY)
    c.drawCentredString(center_x, start_y - gap, f"Matric No: {student.matric_number}")
    c.drawCentredString(center_x, start_y - 2 * gap, f"Department: {student.department}")
    c.drawCentredString(center_x, start_y - 3 * gap, f"Level: {student.level}")
    c.drawCentredString(center_x, start_y - 4 * gap, f"Phone: {student.phone}")

    # ================= SIGNATURE =================
    if application and application.signature:
        try:
            signature_img = image_from_url(application.signature.url)
            c.drawImage(
                signature_img,
                center_left,
                16,
                30,
                11,
                preserveAspectRatio=True,
                mask="auto",
            )
        except Exception as e:
            print(f"Signature load failed: {e}")

    # ================= FOOTER =================
    c.setFont("Helvetica", 5.5)
    c.setFillColor(GRAY)
    c.drawCentredString(CARD_WIDTH / 2, 2, "Property of Ekiti State University")

    c.save()
    buffer.seek(0)

    # ================= UPLOAD TO CLOUDINARY =================
    result = cloudinary.uploader.upload(
        buffer,
        resource_type="raw",
        folder="idcards/pdfs",
        public_id=f"idcard_{id_card.uid}",
        overwrite=True,
    )

    return result
