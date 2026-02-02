from django.shortcuts import render, get_object_or_404
from idcards.models import IDCard


def verify_id(request, uid):
    """
    Public ID verification endpoint (QR target)
    """
    id_card = get_object_or_404(IDCard, uid=uid)

    student = id_card.student

    return render(
        request,
        "idcards/verify.html",
        {
            "student": student,
            "issued_at": id_card.issued_at,
        }
    )
