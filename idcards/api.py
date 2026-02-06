from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.shortcuts import get_object_or_404

from .models import IDCard
from students.models import Student
from idcards.services import ensure_id_card_exists


class MyIDCardAPI(APIView):
    """
    Return logged-in student's ID card download URL (Cloudinary PNG).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            student = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            return Response({"error": "Student profile not found"}, status=404)

        card = IDCard.objects.filter(student=student).first()

        if not card:
            return Response({"error": "ID card not created yet"}, status=404)

        # Ensure image exists (rebuild if missing)
        ensure_id_card_exists(card)

        if not card.image:
            return Response({"error": "ID card not generated yet"}, status=404)

        try:
            url = card.image.url
        except Exception:
            return Response({"error": "ID card unavailable"}, status=500)

        return Response({
            "download_url": url,
            "uid": str(card.uid),
        })


class VerifyIDCardAPI(APIView):
    """
    Public verification endpoint used by QR scan.
    """
    authentication_classes = []
    permission_classes = []

    def get(self, request, uid):

        card = IDCard.objects.filter(uid=uid, is_active=True).select_related("student").first()

        if not card:
            return Response({"valid": False}, status=404)

        student = card.student

        return Response({
            "valid": True,
            "uid": str(card.uid),
            "student": student.matric_number,
            "name": student.full_name if hasattr(student, "full_name") else "",
            "department": student.department,
            "level": student.level,
        })
