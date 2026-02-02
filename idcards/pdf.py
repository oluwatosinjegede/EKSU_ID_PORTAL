import os
import uuid
from pathlib import Path

from django.conf import settings
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing

import requests
from io import BytesIO
from reportlab.lib.utils import ImageReader

# ================= CARD SIZE (ISO ID-1) =================
CARD_WIDTH, CARD_HEIGHT = (85.60 * mm, 53.98 * mm)

# ================= COLORS =================
EKSU_BLUE = HexColor("#8B0000")
DARK = HexColor("#0f172a")
LIGHT_BG = HexColor("#f8fafc")
GRAY = HexColor("#64748b")


def get_student_full_name(student):
    """
    FIRST + MIDDLE + LAST (safe, no double spaces)
    """
    parts = [
        student.user.first_name,
        student.middle_name,
        student.user.last_name,
    ]
    return " ".join(p for p in parts if p)

def image_from_url(url, timeout=10):
    """
    Fetch an image from a remote URL and return an ImageReader.
    Works with Cloudinary, S3, etc.
    """
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return ImageReader(BytesIO(response.content))


def generate_id_card_pdf(id_card):
    student = id_card.student
    application = getattr(student, "idapplication", None)

    # ================= FILE PATHS =================
    relative_path = Path("idcards") / f"{student.matric_number}.pdf"
    final_path = Path(settings.MEDIA_ROOT) / relative_path
    final_path.parent.mkdir(parents=True, exist_ok=True)

    temp_path = final_path.with_name(f".tmp_{uuid.uuid4().hex}.pdf")

    c = canvas.Canvas(str(temp_path), pagesize=(CARD_WIDTH, CARD_HEIGHT))

    # ================= BACKGROUND =================
    c.setFillColor(LIGHT_BG)
    c.rect(0, 0, CARD_WIDTH, CARD_HEIGHT, fill=1)

    # ================= WATERMARK LOGO =================
    logo_path = Path(settings.MEDIA_ROOT) / "branding" / "eksu_logo.png"
    if logo_path.exists():
        c.saveState()
        c.setFillAlpha(0.08)
        wm_size = 42 * mm
        c.drawImage(
            str(logo_path),
            (CARD_WIDTH - wm_size) / 2,
            (CARD_HEIGHT - wm_size) / 2,
            wm_size,
            wm_size,
            preserveAspectRatio=True,
            mask="auto",
        )
        c.restoreState()

    # ================= LEFT ACCENT STRIP =================
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
        "EKITI STATE UNIVERSITY (EKSU)"
    )

    # =====================================================
    # LEFT COLUMN — QR CODE
    # =====================================================
    qr_x = 10
    qr_y = 8

    #verify_url = f"http://127.0.0.1:8000/verify/{id_card.uid}/"
    BASE_URL = settings.SITE_URL
    verify_url = f"{BASE_URL}/verify/{id_card.id}/"

    qr_widget = qr.QrCodeWidget(verify_url)
    bounds = qr_widget.getBounds()

    qr_size = 22 * mm
    bw = bounds[2] - bounds[0]
    bh = bounds[3] - bounds[1]

    qr_drawing = Drawing(
        qr_size,
        qr_size,
        transform=[qr_size / bw, 0, 0, qr_size / bh, 0, 0],
    )
    qr_drawing.add(qr_widget)

    c.setFillColorRGB(1, 1, 1)
    c.roundRect(
        qr_x - 2,
        qr_y - 2,
        qr_size + 4,
        qr_size + 4,
        4,
        fill=1,
        stroke=0,
    )
    qr_drawing.drawOn(c, qr_x, qr_y)

    c.setFont("Helvetica", 5.8)
    c.setFillColor(GRAY)
    c.drawCentredString(qr_x + qr_size / 2, 4, "Scan to verify")

    # =====================================================
    # RIGHT COLUMN — PASSPORT PHOTO (SAME SIZE AS QR)
    # =====================================================
    photo_size = qr_size
    photo_x = CARD_WIDTH - photo_size - 8
    photo_y = 8

    if application and application.passport:
        try:
            passport_img = image_from_url(application.passport.url)

            c.roundRect(
                photo_x - 2,
                photo_y - 2,
                photo_size + 4,
                photo_size + 4,
                4,
                stroke=0,
                fill=0,
            )

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
            # Optional: log instead of crashing PDF generation
            print(f"Passport image load failed: {e}")

    # =====================================================
    # CENTER COLUMN — STUDENT DETAILS
    # =====================================================
    center_left = qr_x + qr_size + 8
    center_right = photo_x - 8
    center_x = (center_left + center_right) / 2

    start_y = CARD_HEIGHT - 46
    gap = 9

    full_name = get_student_full_name(student).upper()

    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 10.5)
    c.drawCentredString(center_x, start_y, full_name)

    c.setFont("Helvetica", 8.5)
    c.setFillColor(GRAY)
    c.drawCentredString(center_x, start_y - gap, f"Matric No: {student.matric_number}")
    c.drawCentredString(center_x, start_y - 2 * gap, f"Department: {student.department}")
    c.drawCentredString(center_x, start_y - 3 * gap, f"Level: {student.level}")
    c.drawCentredString(center_x, start_y - 4 * gap, f"Phone: {student.phone}")

   # ================= SIGNATURE (ABOVE FOOTER) =================
    if application and application.signature:
        try:
            sig_y = 16
            signature_img = image_from_url(application.signature.url)

            c.drawImage(
                signature_img,
                center_left,
                sig_y,
                30,
                11,
                preserveAspectRatio=True,
                mask="auto",
            )

            c.setFont("Helvetica", 5.5)
            c.setFillColor(DARK)
            c.drawString(center_left, sig_y - 3, "Student Signature")

        except Exception as e:
            print(f"Signature image load failed: {e}")

    # ================= FOOTER =================
    c.setFont("Helvetica", 5.5)
    c.setFillColor(GRAY)
    c.drawCentredString(
        CARD_WIDTH / 2,
        2,
        "Property of Ekiti State University"
    )

    c.save()

    # ================= ATOMIC SAVE =================
    os.replace(temp_path, final_path)

    id_card.pdf.name = str(relative_path).replace("\\", "/")
    id_card.save(update_fields=["pdf"])

    return final_path
