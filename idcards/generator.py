import requests
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from django.conf import settings
from django.core.files.base import ContentFile
from io import BytesIO
import os
import qrcode

from applications.models import IDApplication


# =====================================================
# SAFE FONT LOADER
# =====================================================
def load_fonts():
    font_path = os.path.join(settings.BASE_DIR, "static/fonts/DejaVuSans-Bold.ttf")

    try:
        return (
            ImageFont.truetype(font_path, 48),
            ImageFont.truetype(font_path, 32),
            ImageFont.truetype(font_path, 26),
        )
    except Exception:
        default = ImageFont.load_default()
        return default, default, default


# =====================================================
# QR CODE
# =====================================================
def create_qr_code(data):
    qr = qrcode.QRCode(box_size=6, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white").convert("RGB")


# =====================================================
# WATERMARK
# =====================================================
def apply_logo_watermark(card):
    logo_path = os.path.join(settings.BASE_DIR, "static/images/university_logo.png")

    if not os.path.exists(logo_path):
        return card

    try:
        logo = Image.open(logo_path).convert("RGBA")
        w, h = card.size
        logo = logo.resize((int(w * 0.35), int(h * 0.35)))

        alpha = logo.split()[3]
        alpha = ImageEnhance.Brightness(alpha).enhance(0.12)
        logo.putalpha(alpha)

        card.paste(logo, ((w - logo.width) // 2, (h - logo.height) // 2), logo)
    except Exception:
        pass

    return card


# =====================================================
# STUDENT DATA
# =====================================================
def get_student_details(student):
    first = str(getattr(student, "first_name", "") or "").strip()
    middle = str(getattr(student, "middle_name", "") or "").strip()
    last = str(getattr(student, "last_name", "") or "").strip()

    full_name = " ".join(filter(None, [first, middle, last])).strip()

    matric = str(getattr(student, "matric_number", "") or "").strip()
    department = str(getattr(student, "department", "") or "").strip()
    level = str(getattr(student, "level", "") or "").strip()
    phone = str(getattr(student, "phone", "") or "").strip()

    return full_name, matric, department, level, phone


# =====================================================
# LOAD PASSPORT FROM CLOUDINARY URL
# =====================================================
def load_passport(student):
    app = IDApplication.objects.filter(
        student=student,
        status=IDApplication.STATUS_APPROVED
    ).first()

    if not app or not app.passport:
        print("GENERATOR: NO PASSPORT IN APPLICATION")
        return None

    try:
        url = app.passport.url
        response = requests.get(url, timeout=15)

        if response.status_code != 200:
            print("GENERATOR: PASSPORT DOWNLOAD FAILED")
            return None

        photo = Image.open(BytesIO(response.content)).convert("RGB")
        return photo.resize((220, 260))

    except Exception as e:
        print("GENERATOR: PASSPORT LOAD FAILED:", str(e))
        return None


# =====================================================
# MAIN GENERATOR (CLOUDINARY SAFE)
# =====================================================
def generate_id_card(idcard):

    print("GENERATOR: START")

    if not idcard:
        return None

    # Idempotent guard
    if idcard.image and getattr(idcard.image, "public_id", None):
        return idcard.image.url

    student = getattr(idcard, "student", None)
    if not student:
        print("GENERATOR: NO STUDENT")
        return None

    passport = load_passport(student)
    if not passport:
        print("GENERATOR: NO PASSPORT FOUND")
        return None

    # -------------------------------------------------
    # BUILD IMAGE
    # -------------------------------------------------
    width, height = 1010, 640
    card = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(card)

    font_big, font_mid, font_small = load_fonts()

    draw.rectangle((0, 0, width, 120), fill=(0, 102, 0))
    draw.text((30, 30), "EKSU STUDENT ID CARD", font=font_big, fill="white")

    card.paste(passport, (50, 180))

    full_name, matric, dept, level, phone = get_student_details(student)

    draw.text((320, 200), f"Name: {full_name}", font=font_mid, fill="black")
    draw.text((320, 260), f"Matric No: {matric}", font=font_mid, fill="black")
    draw.text((320, 320), f"Department: {dept}", font=font_mid, fill="black")
    draw.text((320, 380), f"Level: {level}", font=font_mid, fill="black")
    draw.text((320, 440), f"Phone: {phone}", font=font_mid, fill="black")

    try:
        verify_url = f"{settings.SITE_URL}/verify/{idcard.uid}/"
        qr_img = create_qr_code(verify_url).resize((160, 160))
        card.paste(qr_img, (820, 380))
    except Exception:
        pass

    draw.rectangle((0, height - 80, width, height), fill=(0, 102, 0))
    draw.text((40, height - 60), "Property of EKSU", font=font_small, fill="white")

    card = apply_logo_watermark(card)

    # -------------------------------------------------
    # SAVE TO CLOUDINARY (FINAL FIX — NEVER FAIL)
    # -------------------------------------------------
    # -------------------------------------------------
    # SAVE TO CLOUDINARY (FINAL PERMANENT FIX)
    # -------------------------------------------------
    try:
        buffer = BytesIO()
        card.save(buffer, format="PNG")
        buffer.seek(0)

        filename = f"{matric or idcard.uid}.png"

        # DO NOT assign idcard.image manually
        field_file = getattr(idcard, "image", None)

        if not field_file:
            print("GENERATOR: FIELD INIT")
            idcard.save(update_fields=[])   # forces Django to attach FieldFile
            field_file = idcard.image

        field_file.save(
            filename,
            ContentFile(buffer.read()),
            save=True
        )

        idcard.refresh_from_db()

        if idcard.image and getattr(idcard.image, "public_id", None):
            print("GENERATOR: SAVE OK", idcard.image.url)
            return idcard.image.url

        print("GENERATOR: SAVE FAILED - EMPTY FIELD")
        return None

    except Exception as e:
        print("GENERATOR SAVE FAILED:", str(e))
        return None
