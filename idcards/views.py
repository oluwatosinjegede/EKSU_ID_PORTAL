from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse
from .models import IDCard


def verify_id_card(request, pk):
    """
    Redirect to Cloudinary-hosted PDF
    """
    id_card = get_object_or_404(IDCard, pk=pk)

    if not id_card.pdf:
        return HttpResponse("ID card not generated", status=404)

    # 🔑 Cloudinary generates correct /raw/upload/ URL here
    return redirect(id_card.pdf.url)
