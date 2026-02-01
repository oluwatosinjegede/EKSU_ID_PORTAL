import os
import qrcode
from django.conf import settings


def generate_qr_code(uid):
    """
    Generates a QR code image for ID verification
    """
    verify_url = f"{settings.SITE_URL}/verify/{uid}"

    qr = qrcode.make(verify_url)

    qr_dir = os.path.join(settings.MEDIA_ROOT, 'qr')
    os.makedirs(qr_dir, exist_ok=True)

    qr_path = os.path.join(qr_dir, f"{uid}.png")
    qr.save(qr_path)

    return qr_path
