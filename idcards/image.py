from io import BytesIO
from pathlib import Path

import cloudinary.uploader
from PIL import Image, ImageDraw, ImageFont
from django.conf import settings
import qrcode


# ================= CARD SIZE (ID-1 @ 300dpi scaled) =================
CARD_WIDTH = 1011   # px
CARD_HEIGHT = 638   # px

# ================= COLORS =================
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


def load_image_from_url(url, size=None):
    img = Image.open(BytesIO(Image.open(BytesIO(requests.get(url).content)).tobytes()))
    if size:
        img = img.resize(size, Image.LANCZOS)
    return img.convert("RGBA")


def generate_id_card_image(id_card) -> dict:
    """
    Generates ID card as JPG and uploads to Cloudinary (IMAGE).
    Returns Cloudinary upload result dict.
    """

    student = id_card.student
    application = getattr(student, "idapplication", None)

    # ================= BASE IMAGE =================
    img = Image.new("RGB", (CARD_WIDTH, CARD_HEIGHT), LIGHT_BG)
    draw = ImageDraw.Draw(img)

    # ================= FONTS =================
    font_dir = Path(settings.BASE_DIR) / "static" / "fonts"
    bold_font = ImageFont.truetype(str(font_dir / "DejaVuSans-Bold.ttf"), 40)
    normal_font = ImageFont.truetype(str(font_dir / "DejaVuSans.ttf"), 30)
    small_font = ImageFont.truetype(str(font_dir / "DejaVuSans.ttf"), 22)

    # ================= HEADER =================
    draw.rectangle([0, 0, CARD_WIDTH, 90], fill=EKSU_BLUE)
    draw.text(
        (CARD_WIDTH // 2 - 380, 25),
        "EKITI STATE UNIVERSITY (EKSU)",
        fill="white",
        font=bold_font,
    )

    # ================= WATERMARK =================
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

    # ================= QR CODE =================
    verify_url = f"{settings.SITE_URL}/verify/{id_card.uid}/"
    qr_img = qrcode.make(verify_url).resize((220, 220))
    img.paste(qr_img, (40, CARD_HEIGHT - 260))

    # ================= PASSPORT =================
    if application and application.passport:
        try:
            passport = Image.open(BytesIO(requests.get(application.passport.url).content))
            passport = passport.resize((220, 260), Image.LANCZOS)
            img.paste(passport, (CARD_WIDTH - 260, CARD_HEIGHT - 300))
        except Exception:
            pass

    # ================= STUDENT DETAILS =================
    y = 140
    gap = 50

    draw.text((320, y), get_student_full_name(student).upper(), fill=DARK, font=bold_font)
    draw.text((320, y + gap), f"Matric No: {student.matric_number}", fill=DARK, font=normal_font)
    draw.text((320, y + 2 * gap), f"Department: {student.department}", fill=DARK, font=normal_font)
    draw.text((320, y + 3 * gap), f"Level: {student.level}", fill=DARK, font=normal_font)
    draw.text((320, y + 4 * gap), f"Phone: {student.phone}", fill=GRAY, font=small_font)

    # ================= SIGNATURE =================
    if application and application.signature:
        try:
            signature = Image.open(BytesIO(requests.get(application.signature.url).content))
            signature = signature.resize((200, 80), Image.LANCZOS)
            img.paste(signature, (320, CARD_HEIGHT - 120))
            draw.text((320, CARD_HEIGHT - 35), "Student Signature", fill=GRAY, font=small_font)
        except Exception:
            pass

    # ================= EXPORT =================
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=95, subsampling=0)
    buffer.seek(0)

    # ================= UPLOAD TO CLOUDINARY =================
    result = cloudinary.uploader.upload(
        buffer,
        resource_type="image",
        folder="idcards/images",
        public_id=f"idcard_{id_card.uid}",
        overwrite=True,
    )

    return result
