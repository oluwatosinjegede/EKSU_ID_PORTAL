from django.http import HttpResponse, FileResponse, Http404
from django.shortcuts import get_object_or_404
from .models import IDCard
from .services import ensure_id_card_exists
import os
from django.conf import settings


def verify_id(request, uid):
    id_card = get_object_or_404(IDCard, uid=uid)

    # Rebuild image if missing (Railway safe)
    ensure_id_card_exists(id_card)

    if not id_card.image:
        return HttpResponse("ID Card not generated", status=404)

    file_path = os.path.join(settings.MEDIA_ROOT, id_card.image.name)

    if not os.path.exists(file_path):
        raise Http404("ID image missing")

    return FileResponse(open(file_path, "rb"), content_type="image/png")
