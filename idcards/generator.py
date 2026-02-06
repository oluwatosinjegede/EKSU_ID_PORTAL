from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from django.conf import settings
import os
import qrcode

from io import BytesIO
from django.core.files.base import ContentFile





# =========================
# SAFE FONT LOADER
# =========================
def load_fonts():
    font_path = os.path.join(settings.BASE_DIR, "static/fonts/DejaVuSans-Bold.ttf")

    try:
        return (
            ImageFont.truetype(font_path, 48),
            ImageFont.truetype(font_path, 32),
            ImageFont.truetype(font_path, 26),
        )
    except Exception:
        return (
            ImageFont.load_default(),
            ImageFont.load_default(),
            ImageFont.load_default(),
        )


# =========================
# QR CODE
# =========================
def create_qr_code(data):
    qr = qrcode.QRCode(box_size=6, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white").convert("RGB")


# =========================
# WATERMARK
# =========================
def apply_logo_watermark(card):
    logo_path = os.path.join(settings.BASE_DIR, "static/images/university_logo.png")

    if not os.path.exists(logo_path):
        return card

    logo = Image.open(logo_path).convert("RGBA")

    w, h = card.size
    logo = logo.resize((int(w * 0.35), int(h * 0.35)))

    alpha = logo.split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(0.12)
    logo.putalpha(alpha)

    card.paste(logo, ((w - logo.width) // 2, (h - logo.height) // 2), logo)
    return card


# =========================
# SAFE STUDENT DATA
# =========================
def get_student_details(student):

    first = str(getattr(student, "first_name", "") or "").strip()
    middle = str(getattr(student, "middle_name", "") or "").strip()
    last = str(getattr(student, "last_name", "") or "").strip()

    # FULL NAME ALWAYS SAFE
    full_name = " ".join(filter(None, [first, middle, last])).strip()

    matric = str(getattr(student, "matric_no", "") or "").strip()
    department = str(getattr(student, "department", "") or "").strip()
    level = str(getattr(student, "level", "") or "").strip()
    phone = str(getattr(student, "phone", "") or "").strip()

    return full_name, matric, department, level, phone


# =========================
# SAFE PASSPORT LOADER
# =========================
def paste_passport(card, idcard):
    try:
        if idcard.passport:
            idcard.passport.open("rb")
            photo = Image.open(idcard.passport).convert("RGB")
            photo = photo.resize((220, 260))
            card.paste(photo, (50, 180))
    except Exception:
        pass

# =========================
# MAIN GENERATOR (Cloudinary)
# =========================

def generate_id_card(idcard):

    student = idcard.student

    width, height = 1010, 640
    card = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(card)

    font_big, font_mid, font_small = load_fonts()

    # ================= HEADER =================
    draw.rectangle((0, 0, width, 120), fill=(0, 102, 0))
    draw.text((30, 30), "EKSU STUDENT ID CARD", font=font_big, fill="white")

    # ================= PASSPORT =================
    paste_passport(card, idcard)

    # ================= STUDENT DATA =================
    full_name, matric, dept, level, phone = get_student_details(student)

    draw.text((320, 200), f"Name: {full_name}", font=font_mid, fill="black")
    draw.text((320, 260), f"Matric No: {matric}", font=font_mid, fill="black")
    draw.text((320, 320), f"Department: {dept}", font=font_mid, fill="black")
    draw.text((320, 380), f"Level: {level}", font=font_mid, fill="black")
    draw.text((320, 440), f"Phone: {phone}", font=font_mid, fill="black")

    # ================= QR CODE =================
    verify_url = f"{settings.SITE_URL}/verify/{idcard.uid}/"
    qr_img = create_qr_code(verify_url).resize((160, 160))
    card.paste(qr_img, (820, 380))

    # ================= FOOTER =================
    draw.rectangle((0, height - 80, width, height), fill=(0, 102, 0))
    draw.text((40, height - 60), "Property of EKSU", font=font_small, fill="white")

    # ================= WATERMARK =================
    card = apply_logo_watermark(card)

    # ================= SAVE TO CLOUDINARY =================

    # Save image to memory buffer (not filesystem)
    buffer = BytesIO()
    card.save(buffer, format="PNG")
    buffer.seek(0)

    filename = f"idcards/{matric or idcard.uid}.png"

    # Save via Django storage (Cloudinary backend)
    idcard.image.save(
        filename,
        ContentFile(buffer.read()),
        save=True,
    )

    return idcard.image.url
