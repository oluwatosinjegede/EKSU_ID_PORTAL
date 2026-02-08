from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from .models import IDCard
from .services import ensure_id_card_exists



def verify_id(request, uid):
    id_card = get_object_or_404(IDCard, uid=uid)

    # Ensure ID exists (rebuild if missing)
    ensure_id_card_exists(id_card)

    # If still no image ? invalid ID
    if not id_card.image:
        return HttpResponse("ID Card not generated", status=404)

    try:
        image_url = id_card.image.url
    except Exception:
        raise Http404("ID image unavailable")

    # Redirect browser to Cloudinary-hosted image
    return redirect(image_url)



def download_id(request, uid):
    id_card = get_object_or_404(IDCard, uid=uid)

    # Ensure image exists
    ensure_id_card_exists(id_card)

    if not id_card.image:
        raise Http404("ID not generated")

    try:
        image_url = id_card.image.url
    except Exception:
        raise Http404("Image unavailable")

    # Force download from Cloudinary
    return redirect(f"{image_url}?fl_attachment")


def view_id_card(request):
    student = request.user.student
    idcard = getattr(student, "id_card", None)

    if not idcard:
        return HttpResponse("No ID card", status=404)

    result = generate_id_card(idcard)

    if not result:
        return HttpResponse("ID generation failed", status=500)

    # If Cloudinary saved ? result is URL
    if isinstance(result, str):
        return redirect(result)

    # If failover ? result is raw image bytes
    response = HttpResponse(result, content_type="image/png")
    response["Content-Disposition"] = "inline; filename=id_card.png"
    return response

