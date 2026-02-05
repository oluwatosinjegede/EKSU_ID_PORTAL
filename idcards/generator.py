from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from django.conf import settings
import os
import qrcode


# =========================
# QR CODE GENERATOR
# =========================
def create_qr_code(data):
    qr = qrcode.QRCode(
        version=1,
        box_size=6,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    return img.convert("RGB")


# =========================
# WATERMARK (UNIVERSITY LOGO)
# =========================
def apply_logo_watermark(base_img):
    """
    Adds semi-transparent university logo watermark at center
    """

    logo_path = os.path.join(settings.MEDIA_ROOT, "template/university_logo.png")

    if not os.path.exists(logo_path):
        return base_img  # Skip if logo missing

    logo = Image.open(logo_path).convert("RGBA")

    # Resize logo relative to card
    w, h = base_img.size
    logo = logo.resize((int(w * 0.45), int(h * 0.45)))

    # Make watermark transparent
    alpha = logo.split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(0.15)  # transparency level
    logo.putalpha(alpha)

    # Position center
    lx = (w - logo.width) // 2
    ly = (h - logo.height) // 2

    base_img.paste(logo, (lx, ly), logo)

    return base_img


# =========================
# MAIN GENERATOR
# =========================
def generate_id_card(idcard):
    if not idcard:
        raise ValueError("IDCard instance is None")

    student = idcard.student

    # Canvas size
    width, height = 1010, 640
    card = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(card)

    # =========================
    # FONTS (Raspberry Pi safe)
    # =========================
    font_path = os.path.join(settings.BASE_DIR, "static/fonts/DejaVuSans-Bold.ttf")

    font_big = ImageFont.truetype(font_path, 48)
    font_mid = ImageFont.truetype(font_path, 32)
    font_small = ImageFont.truetype(font_path, 26)

    # =========================
    # HEADER
    # =========================
    draw.rectangle((0, 0, width, 120), fill=(0, 102, 0))
    draw.text((30, 30), "EKSU STUDENT ID CARD", font=font_big, fill="white")

    # =========================
    # PASSPORT PHOTO
    # =========================
    if idcard.passport and os.path.exists(idcard.passport.path):
        photo = Image.open(idcard.passport.path).resize((220, 260))
        card.paste(photo, (50, 180))

    # =========================
    # STUDENT DETAILS
    # =========================
    draw.text((320, 200), f"Name: {student.full_name}", font=font_mid, fill="black")
    draw.text((320, 260), f"Matric No: {student.matric_no}", font=font_mid, fill="black")
    draw.text((320, 320), f"Department: {student.department}", font=font_mid, fill="black")
    draw.text((320, 380), f"Faculty: {student.faculty}", font=font_mid, fill="black")
    draw.text((320, 440), f"Session: {student.session}", font=font_mid, fill="black")

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
    # APPLY WATERMARK (LOGO)
    # =========================
    card = apply_logo_watermark(card)

    # =========================
    # SAVE IMAGE
    # =========================
    output_dir = os.path.join(settings.MEDIA_ROOT, "idcards")
    os.makedirs(output_dir, exist_ok=True)

    filename = f"{student.matric_no}.png"
    output_path = os.path.join(output_dir, filename)

    card.save(output_path, "PNG")

    # Update model
    idcard.image.name = f"idcards/{filename}"
    idcard.save()

    return output_path
