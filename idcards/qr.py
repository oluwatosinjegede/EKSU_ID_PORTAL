import qrcode
from io import BytesIO
from django.conf import settings
import cloudinary.uploader


def generate_qr_code(id_card):
    """
    Generate QR code and upload to Cloudinary.
    Encodes full verification URL.
    Railway-safe (no filesystem).
    """

    if not id_card or not id_card.uid:
        raise ValueError("Invalid IDCard")

    # QR should encode full verification link (recommended)
    verify_url = f"{settings.SITE_URL}/verify/{id_card.uid}/"

    # Build QR image in memory
    qr = qrcode.QRCode(box_size=6, border=2)
    qr.add_data(verify_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    public_id = f"idcards/qr/{id_card.uid}"

    try:
        result = cloudinary.uploader.upload(
            buffer,
            resource_type="image",
            public_id=public_id,
            overwrite=True,
        )
        return result.get("secure_url")

    except Exception:
        # Never crash ID generation if QR upload fails
        return None
