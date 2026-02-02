# idcards/qr.py

import qrcode
from io import BytesIO
import cloudinary.uploader


def generate_qr_code(id_card):
    """
    Generate QR code in memory and upload to Cloudinary.
    No filesystem usage. Railway-safe.
    """

    # What the QR encodes (keep this consistent with your verify logic)
    data = str(id_card.uid)

    qr = qrcode.make(data)

    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)

    result = cloudinary.uploader.upload(
        buffer,
        resource_type="image",
        folder="idcards/qr",
        public_id=str(id_card.uid),
        overwrite=True,
    )

    # Optional: store URL if you add a field later
    # id_card.qr_url = result["secure_url"]
    # id_card.save(update_fields=["qr_url"])

    return result["secure_url"]
