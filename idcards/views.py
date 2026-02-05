from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from .models import IDCard


def verify_id(request, uid):
    """
    Verify ID card via QR code.
    """
    id_card = get_object_or_404(IDCard, uid=uid, is_active=True)

    return HttpResponse(
        f"ID Card Verified for {id_card.student.full_name}",
        content_type="text/plain",
    )
