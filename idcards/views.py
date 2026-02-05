from django.http import JsonResponse, Http404
from .models import IDCard


def verify_id_card(request, uid):
    try:
        card = IDCard.objects.select_related("student").get(uid=uid)
    except IDCard.DoesNotExist:
        raise Http404("Invalid ID Card")

    student = card.student

    return JsonResponse({
        "status": "VALID",
        "name": student.full_name,
        "matric": student.matric_number,
        "department": student.department,
        "faculty": student.faculty,
    })
