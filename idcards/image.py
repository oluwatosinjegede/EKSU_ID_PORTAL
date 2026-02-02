from io import BytesIO
from pathlib import Path

import requests
import cloudinary.uploader
from PIL import Image, ImageDraw, ImageFont
from django.conf import settings
import qrcode


CARD_WIDTH = 1011
CARD_HEIGHT = 638

EKSU_BLUE = "#8B0000"
DARK = "#0f172a"
LIGHT_BG = "#f8fafc"
GRAY = "#64748b"


def get_student_full_name(student):
    parts = [
        student.user.first_name,
        student.middle_name,
        student.user.last_name,
    ]
    return " ".join(p for p in parts if p)


def load_image_from_url(url, size=None, mode="RGBA"):
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    img = Image.open(BytesIO(resp.content))
    if size:
        img = img.resize(size, Image.LANCZOS)
    return img.convert(mode)


def generate_id_card_image(id_card) -> dict:
    student = id_card.student
    application = getattr(student, "idapplication", None)

    img = Image.new("RGB", (CARD_WIDTH, CARD_HEIGHT), LIGHT_BG)
    draw = ImageDraw.Draw(img)

    font_dir = Path(settings.BASE_DIR) / "static" / "fonts"
    bold_font = ImageFont.truetype(str(font_dir / "DejaVuSans-Bold.ttf"), 40)
    normal_font = ImageFont.truetype(str(font_dir / "DejaVuSans.ttf"), 30)
    small_font = ImageFont.truetype(str(font_dir / "DejaVuSans.ttf"), 22)

    draw.rectangle([0, 0, CARD_WIDTH, 90], fill=EKSU_BLUE)
    draw.text(
        (CARD_WIDTH // 2 - 380, 25),
        "EKITI STATE UNIVERSITY (EKSU)",
        fill="white",
        font=bold_font,
    )

    watermark_path = Path(settings.BASE_DIR) / "static" / "images" / "eksu_logo.png"
    if watermark_path.exists():
        watermark = Image.open(watermark_path).convert("RGBA")
        watermark = watermark.resize((300, 300), Image.LANCZOS)
        watermark.putalpha(30)
        img.paste(
            watermark,
            ((CARD_WIDTH - 300) // 2, (CARD_HEIGHT - 300) // 2),
            watermark,
        )

    verify_url = f"{settings.SITE_URL}/verify/{id_card.uid}/"
    qr_img = qrcode.make(verify_url).resize((220, 220))
    img.paste(qr_img, (40, CARD_HEIGHT - 260))

    if application and application.passport:
        try:
            passport = load_image_from_url(
                application.passport.url, size=(220, 260), mode="RGB"
            )
            img.paste(passport, (CARD_WIDTH - 260, CARD_HEIGHT - 300))
        except Exception:
            pass

    y = 140
    gap = 50

    draw.text((320, y), get_student_full_name(student).upper(), fill=DARK, font=bold_font)
    draw.text((320, y + gap), f"Matric No: {student.matric_number}", fill=DARK, font=normal_font)
    draw.text((320, y + 2 * gap), f"Department: {student.department}", fill=DARK, font=normal_font)
    draw.text((320, y + 3 * gap), f"Level: {student.level}", fill=DARK, font=normal_font)
    draw.text((320, y + 4 * gap), f"Phone: {student.phone}", fill=GRAY, font=small_font)

    if application and application.signature:
        try:
            signature = load_image_from_url(
                application.signature.url, size=(200, 80), mode="RGB"
            )
            img.paste(signature, (320, CARD_HEIGHT - 120))
            draw.text((320, CARD_HEIGHT - 35), "Student Signature", fill=GRAY, font=small_font)
        except Exception:
            pass

    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=95, subsampling=0)
    buffer.seek(0)

    result = cloudinary.uploader.upload(
        buffer,
        resource_type="image",
        folder="idcards/images",
        public_id=f"idcard_{id_card.uid}",
        overwrite=True,
    )

    return result
