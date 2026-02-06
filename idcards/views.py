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
