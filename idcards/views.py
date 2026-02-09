from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

from .models import IDCard
from .services import ensure_id_card_exists
from .generator import generate_id_card

from django.shortcuts import render
from django.http import Http404



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

def verify_id(request, uid, token=None):

    id_card = get_object_or_404(IDCard, uid=uid)

    # -------------------------
    # TOKEN VALIDATION (ANTI-FORGE)
    # -------------------------

    if token and id_card.verify_token != token:
        return render(request, "idcards/verify_invalid.html", {"valid": False})

    # -------------------------
    # REVOKED / DISABLED CHECK
    # -------------------------
    if not id_card.is_active or id_card.is_revoked:
        return render(request, "idcards/verify_revoked.html", {
            "reason": id_card.revoked_reason
        })

    # -------------------------
    # SELF HEAL
    # -------------------------
    ensure_id_card_exists(id_card)
    id_card.refresh_from_db()

    student = id_card.student

    # -------------------------
    # IMAGE SOURCE
    # -------------------------
    image_url = None
    image_stream_url = None

    if id_card.image and getattr(id_card.image, "url", None):
        image_url = id_card.image.url
    else:
        image_stream_url = f"/stream/{id_card.uid}/"

    return render(request, "idcards/verify.html", {
        "valid": True,
        "student": student,
        "id_card": id_card,
        "image_url": image_url,
        "image_stream_url": image_stream_url,
    })


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
