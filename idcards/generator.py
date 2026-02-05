from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from django.conf import settings
import os
import qrcode


# =========================
# SAFE FONT LOADER
# =========================
def load_fonts():
    font_path = os.path.join(settings.BASE_DIR, "static/fonts/DejaVuSans-Bold.ttf")

    try:
        font_big = ImageFont.truetype(font_path, 48)
        font_mid = ImageFont.truetype(font_path, 32)
        font_small = ImageFont.truetype(font_path, 26)
    except Exception:
        font_big = ImageFont.load_default()
        font_mid = ImageFont.load_default()
        font_small = ImageFont.load_default()

    return font_big, font_mid, font_small


# =========================
# QR CODE GENERATOR
# =========================
def create_qr_code(data):
    qr = qrcode.QRCode(version=1, box_size=6, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white").convert("RGB")


# =========================
# WATERMARK
# =========================
def apply_logo_watermark(base_img):
    logo_path = os.path.join(settings.MEDIA_ROOT, "template/university_logo.png")

    if not os.path.exists(logo_path):
        return base_img

    logo = Image.open(logo_path).convert("RGBA")

    w, h = base_img.size
    logo = logo.resize((int(w * 0.45), int(h * 0.45)))

    alpha = logo.split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(0.15)
    logo.putalpha(alpha)

    lx = (w - logo.width) // 2
    ly = (h - logo.height) // 2

    base_img.paste(logo, (lx, ly), logo)
    return base_img


# =========================
# SAFE STUDENT FIELD ACCESS
# =========================
def get_student_details(student):
    first = getattr(student, "first_name", "") or ""
    middle = getattr(student, "middle_name", "") or ""
    last = getattr(student, "last_name", "") or ""

    full_name = " ".join(filter(None, [first, middle, last])).strip()

    matric = getattr(student, "matric_no", "") or ""
    department = getattr(student, "department", "") or ""
    level = getattr(student, "level", "") or ""
    phone = getattr(student, "phone", "") or ""

    return full_name, matric, department, level, phone


# =========================
# MAIN GENERATOR
# =========================
def generate_id_card(idcard):
    if not idcard:
        raise ValueError("IDCard instance is None")

    student = idcard.student

    # Canvas
    width, height = 1010, 640
    card = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(card)

    # Fonts
    font_big, font_mid, font_small = load_fonts()

    # =========================
    # HEADER
    # =========================
    draw.rectangle((0, 0, width, 120), fill=(0, 102, 0))
    draw.text((30, 30), "EKSU STUDENT ID CARD", font=font_big, fill="white")

    # =========================
    # PASSPORT PHOTO
    # =========================
    if getattr(idcard, "passport", None):
        try:
            if idcard.passport.path and os.path.exists(idcard.passport.path):
                photo = Image.open(idcard.passport.path).resize((220, 260))
                card.paste(photo, (50, 180))
        except Exception:
            pass

    # =========================
    # STUDENT DETAILS
    # =========================
    full_name, matric, dept, level, phone = get_student_details(student)

    draw.text((320, 200), f"Name: {full_name}", font=font_mid, fill="black")
    draw.text((320, 260), f"Matric No: {matric}", font=font_mid, fill="black")
    draw.text((320, 320), f"Department: {dept}", font=font_mid, fill="black")
    draw.text((320, 380), f"Level: {level}", font=font_mid, fill="black")
    draw.text((320, 440), f"Phone: {phone}", font=font_mid, fill="black")

    # =========================
    # QR CODE
    # =========================
    verify_url = f"{settings.SITE_URL}/verify/{idcard.uid}/"
    qr_img = create_qr_code(verify_url).resize((140, 140))
    card.paste(qr_img, (820, 460))

    # =========================
    # FOOTER
    # =========================
    draw.rectangle((0, height - 80, width, height), fill=(0, 102, 0))
    draw.text((40, height - 60), "Property of EKSU", font=font_small, fill="white")

    # =========================
    # WATERMARK
    # =========================
    card = apply_logo_watermark(card)

    # =========================
    # SAVE LOCALLY
    # =========================
    output_dir = os.path.join(settings.MEDIA_ROOT, "idcards")
    os.makedirs(output_dir, exist_ok=True)

    filename = f"{matric or idcard.uid}.png"
    output_path = os.path.join(output_dir, filename)

    card.save(output_path, "PNG")

    # Update model safely
    if hasattr(idcard, "image"):
        idcard.image.name = f"idcards/{filename}"
        idcard.save(update_fields=["image"])

    return output_path
