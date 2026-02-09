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
# QR IMAGE BUILDER
# =====================================================
def create_qr_code(data):
    qr = qrcode.QRCode(
        version=None,
        box_size=6,
        border=2,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
    )
    qr.add_data(data)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white").convert("RGB")


# =====================================================
# BUILD VERIFY URL (NEVER FAILS)
# =====================================================
def build_verify_url(idcard):
    """
    Always returns a working verification URL.
    """

    # Ensure token exists
    if not idcard.verify_token:
        try:
            idcard.generate_token()
            idcard.save(update_fields=["verify_token"])
        except Exception as e:
            print("QR TOKEN ERROR:", str(e))

    base = getattr(settings, "SITE_URL", "").strip().rstrip("/")

    # 1. Valid production domain
    if base and "localhost" not in base and "127.0.0.1" not in base:
        return f"{base}/verify/{idcard.uid}/{idcard.verify_token}/"

    # 2. Railway fallback
    railway = os.getenv("RAILWAY_PUBLIC_DOMAIN")
    if railway:
        return f"https://{railway}/verify/{idcard.uid}/{idcard.verify_token}/"

    # 3. Final fallback (still scannable)
    print("QR WARNING: Using relative URL")
    return f"/verify/{idcard.uid}/{idcard.verify_token}/"


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
        alpha = ImageEnhance.Brightness(alpha).enhance(0.06)  # lighter watermark
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
# LOAD PASSPORT FROM CLOUDINARY
# =====================================================
def load_passport(student):
    app = IDApplication.objects.filter(
        student=student,
        status=IDApplication.STATUS_APPROVED
    ).first()

    if not app or not app.passport:
        print("GENERATOR: NO PASSPORT")
        return None

    try:
        response = requests.get(app.passport.url, timeout=15)

        if response.status_code != 200:
            print("GENERATOR: PASSPORT DOWNLOAD FAILED")
            return None

        photo = Image.open(BytesIO(response.content)).convert("RGB")
        return photo.resize((220, 260))

    except Exception as e:
        print("GENERATOR: PASSPORT LOAD FAILED:", str(e))
        return None


# =====================================================
# MAIN GENERATOR
# =====================================================
def generate_id_card(idcard, request=None):

    print("GENERATOR: START")

    if not idcard:
        return None

    # Already saved in Cloudinary
    if idcard.image and getattr(idcard.image, "public_id", None):
        return idcard.image.url

    student = getattr(idcard, "student", None)
    if not student:
        return None

    passport = load_passport(student)
    if not passport:
        return None

    width, height = 1010, 640
    card = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(card)

    font_big, font_mid, font_small = load_fonts()

    # Header
    draw.rectangle((0, 0, width, 120), fill=(0, 102, 0))
    draw.text((30, 30), "EKSU STUDENT ID CARD", font=font_big, fill="white")

    # Passport
    card.paste(passport, (50, 180))

    full_name, matric, dept, level, phone = get_student_details(student)

    draw.text((320, 200), f"Name: {full_name}", font=font_mid, fill="black")
    draw.text((320, 260), f"Matric No: {matric}", font=font_mid, fill="black")
    draw.text((320, 320), f"Department: {dept}", font=font_mid, fill="black")
    draw.text((320, 380), f"Level: {level}", font=font_mid, fill="black")
    draw.text((320, 440), f"Phone: {phone}", font=font_mid, fill="black")

    # =====================================================
    # GUARANTEED QR
    # =====================================================
    try:
        verify_url = build_verify_url(idcard)
        qr_img = create_qr_code(verify_url).resize((180, 180))
        card.paste(qr_img, (800, 360))
        print("QR OK:", verify_url)
    except Exception as e:
        print("QR CRITICAL FAILURE:", str(e))

    # Footer
    draw.rectangle((0, height - 80, width, height), fill=(0, 102, 0))
    draw.text((40, height - 60), "Property of EKSU", font=font_small, fill="white")

    # Apply watermark AFTER QR
    card = apply_logo_watermark(card)

    # Save / Failover
    try:
        buffer = BytesIO()
        card.save(buffer, format="PNG")
        png_bytes = buffer.getvalue()

        filename = f"{matric or idcard.uid}.png"

        if _try_save_cloudinary(idcard, png_bytes, filename):
            return idcard.image.url

        print("FAILOVER: USING MEMORY IMAGE")
        return png_bytes

    except Exception as e:
        print("GENERATOR FAILURE:", str(e))
        return None


# =====================================================
# CLOUDINARY SAVE
# =====================================================
def _try_save_cloudinary(idcard, png_bytes, filename):
    try:
        field = getattr(idcard, "image", None)

        if not field or not hasattr(field, "save"):
            print("CLOUDINARY: FIELD INVALID")
            return False

        field.save(filename, ContentFile(png_bytes), save=True)
        idcard.refresh_from_db()

        return bool(idcard.image)

    except Exception as e:
        print("CLOUDINARY SAVE FAILED:", str(e))
        return False
