from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, redirect

from .models import IDCard
from .services import ensure_id_card_exists
from .generator import generate_id_card


# =====================================================
# VERIFY ID (Public verification via QR)
# Supports Cloudinary + Failover Stream
# =====================================================
def verify_id(request, uid):
    id_card = get_object_or_404(IDCard, uid=uid)

    # Ensure image exists (self-heal)
    ensure_id_card_exists(id_card)
    id_card.refresh_from_db()

    # -------------------------------
    # CLOUDINARY MODE
    # -------------------------------
    if id_card.image and getattr(id_card.image, "url", None):
        return redirect(id_card.image.url)

    # -------------------------------
    # FAILOVER STREAM MODE
    # -------------------------------
    result = generate_id_card(id_card)

    if isinstance(result, (bytes, bytearray)):
        return HttpResponse(result, content_type="image/png")

    raise Http404("ID Card unavailable")


# =====================================================
# DOWNLOAD ID (Force download)
# Supports Cloudinary + Failover Stream
# =====================================================
def download_id(request, uid):
    id_card = get_object_or_404(IDCard, uid=uid)

    ensure_id_card_exists(id_card)
    id_card.refresh_from_db()

    # -------------------------------
    # CLOUDINARY MODE
    # -------------------------------
    if id_card.image and getattr(id_card.image, "url", None):
        return redirect(f"{id_card.image.url}?fl_attachment")

    # -------------------------------
    # FAILOVER STREAM MODE
    # -------------------------------
    result = generate_id_card(id_card)

    if isinstance(result, (bytes, bytearray)):
        response = HttpResponse(result, content_type="image/png")
        response["Content-Disposition"] = f'attachment; filename="ID-{uid}.png"'
        return response

    raise Http404("ID not generated")


# =====================================================
# STUDENT VIEW ID (Inline display)
# Supports Cloudinary + Failover
# =====================================================
def view_id_card(request):
    if not hasattr(request.user, "student"):
        raise Http404("Student not found")

    id_card = getattr(request.user.student, "id_card", None)

    if not id_card:
        raise Http404("No ID card")

    ensure_id_card_exists(id_card)
    id_card.refresh_from_db()

    # -------------------------------
    # CLOUDINARY MODE
    # -------------------------------
    if id_card.image and getattr(id_card.image, "url", None):
        return redirect(id_card.image.url)

    # -------------------------------
    # FAILOVER STREAM MODE
    # -------------------------------
    result = generate_id_card(id_card)

    if isinstance(result, (bytes, bytearray)):
        response = HttpResponse(result, content_type="image/png")
        response["Content-Disposition"] = "inline; filename=id_card.png"
        return response

    raise Http404("ID generation failed")
