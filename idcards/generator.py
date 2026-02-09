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
    qr = qrcode.QRCode(box_size=6, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white").convert("RGB")


# =====================================================
# BUILD VERIFY URL (NO LOCALHOST IN PROD)
# =====================================================
def build_verify_url(idcard, request=None):
    """
    Build secure verification URL with token.
    Priority:
    1. Current request domain (best for Railway / proxy)
    2. SITE_URL env
    """

    try:
        # ---- Detect domain ----
        if request:
            scheme = "https" if request.is_secure() else "http"
            host = request.get_host()
            base = f"{scheme}://{host}"
        else:
            base = getattr(settings, "SITE_URL", "").strip()

        if not base:
            print("QR: SITE_URL missing")
            return None

        base = base.rstrip("/")

        # Block localhost in production
        if "localhost" in base or "127.0.0.1" in base:
            print("QR: BLOCKED LOCALHOST DOMAIN")
            return None

        # ---- TOKENIZED SECURE VERIFY URL ----
        token = getattr(idcard, "verify_token", None)

        if token:
            url = f"{base}/verify/{idcard.uid}/{token}/"
        else:
            # Backward compatibility (old cards)
            url = f"{base}/verify/{idcard.uid}/"

        return url

    except Exception as e:
        print("QR URL BUILD FAILED:", str(e))
        return None


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

    draw.rectangle((0, 0, width, 120), fill=(0, 102, 0))
    draw.text((30, 30), "EKSU STUDENT ID CARD", font=font_big, fill="white")

    card.paste(passport, (50, 180))

    full_name, matric, dept, level, phone = get_student_details(student)

    draw.text((320, 200), f"Name: {full_name}", font=font_mid, fill="black")
    draw.text((320, 260), f"Matric No: {matric}", font=font_mid, fill="black")
    draw.text((320, 320), f"Department: {dept}", font=font_mid, fill="black")
    draw.text((320, 380), f"Level: {level}", font=font_mid, fill="black")
    draw.text((320, 440), f"Phone: {phone}", font=font_mid, fill="black")

    # =====================================================
    # QR CODE (FIXED DOMAIN)
    # =====================================================
    try:
        verify_url = build_verify_url(idcard, request)

        if verify_url:
            qr_img = create_qr_code(verify_url).resize((160, 160))
            card.paste(qr_img, (820, 380))
            print("QR:", verify_url)
        else:
            print("QR: NOT GENERATED")

    except Exception as e:
        print("QR FAILED:", str(e))

    draw.rectangle((0, height - 80, width, height), fill=(0, 102, 0))
    draw.text((40, height - 60), "Property of EKSU", font=font_small, fill="white")

    card = apply_logo_watermark(card)

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
