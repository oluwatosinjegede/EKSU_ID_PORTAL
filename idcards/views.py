from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

from .models import IDCard
from .services import ensure_id_card_exists
from .generator import generate_id_card


# =====================================================
# INTERNAL HELPER
# Handles Cloudinary + Failover consistently
# =====================================================
def _serve_id_image(id_card, download=False):
    """
    Unified image serving engine.

    Priority:
    1. Cloudinary image (if valid)
    2. Failover generated image (memory)
    """

    # -------------------------------
    # CLOUDINARY MODE
    # -------------------------------
    if id_card.image and getattr(id_card.image, "url", None):
        if download:
            return redirect(f"{id_card.image.url}?fl_attachment")
        return redirect(id_card.image.url)

    # -------------------------------
    # FAILOVER MODE (Generate in-memory)
    # -------------------------------
    result = generate_id_card(id_card)

    if isinstance(result, (bytes, bytearray)):
        response = HttpResponse(result, content_type="image/png")

        if download:
            response["Content-Disposition"] = f'attachment; filename="ID-{id_card.uid}.png"'
        else:
            response["Content-Disposition"] = "inline; filename=id_card.png"

        return response

    raise Http404("ID Card unavailable")


# =====================================================
# VERIFY ID (Public via QR)
# =====================================================
def verify_id(request, uid):
    id_card = get_object_or_404(IDCard, uid=uid)

    # Self-heal if broken
    ensure_id_card_exists(id_card)
    id_card.refresh_from_db()

    return _serve_id_image(id_card, download=False)


# =====================================================
# DOWNLOAD ID (Cloudinary + Failover)
# =====================================================
def download_id(request, uid):
    id_card = get_object_or_404(IDCard, uid=uid)

    ensure_id_card_exists(id_card)
    id_card.refresh_from_db()

    return _serve_id_image(id_card, download=True)


# =====================================================
# STREAM VIEW (Explicit Failover Endpoint)
# Used by dashboard image preview
# =====================================================
@login_required
def view_id_card(request, uid=None):
    """
    Supports:
    - Logged-in student (/my-id/)
    - Stream by UID (/stream/<uid>/)
    """

    if uid:
        id_card = get_object_or_404(IDCard, uid=uid)
    else:
        student = getattr(request.user, "student", None)
        if not student or not hasattr(student, "id_card"):
            raise Http404("No ID card")

        id_card = student.id_card

    ensure_id_card_exists(id_card)
    id_card.refresh_from_db()

    return _serve_id_image(id_card, download=False)

# =====================================================
# STREAM DOWNLOAD (Explicit Failover Download)
# =====================================================
def download_id_stream(request, uid):
    id_card = get_object_or_404(IDCard, uid=uid)

    ensure_id_card_exists(id_card)
    id_card.refresh_from_db()

    return _serve_id_image(id_card, download=True)
