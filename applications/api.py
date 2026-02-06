from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from django.shortcuts import get_object_or_404
from django.db import transaction

from .serializers import IDApplicationSerializer
from .models import IDApplication
from students.models import Student
from accounts.permissions import IsApprover
from idcards.services import generate_id_card


# ======================================================
# APPLY FOR ID (PASSPORT ONLY)
# ======================================================
class ApplyForIDAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        student = get_object_or_404(Student, user=request.user)

        # Prevent duplicate application
        if IDApplication.objects.filter(student=student).exists():
            return Response(
                {"error": "Application already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = IDApplicationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            serializer.save(student=student)
        except Exception as e:
            print("API UPLOAD ERROR:", e)
            return Response(
                {"error": "Passport upload failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"status": "Application submitted successfully"},
            status=status.HTTP_201_CREATED,
        )


# ======================================================
# APPROVE APPLICATION + GENERATE ID
# ======================================================
class ApproveApplicationAPI(APIView):
    permission_classes = [IsApprover]

    def post(self, request, app_id):
        application = get_object_or_404(IDApplication, id=app_id)

        # Prevent duplicate approval
        if application.status == IDApplication.STATUS_APPROVED:
            return Response(
                {"message": "Application already approved"},
                status=status.HTTP_200_OK,
            )

        # Passport must exist
        if not application.passport:
            return Response(
                {"error": "Passport photo missing"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                application.status = IDApplication.STATUS_APPROVED
                application.reviewed_by = request.user.username
                application.save(update_fields=["status", "reviewed_by"])

                # Generate ID card (idempotent)
                generate_id_card(application)

        except Exception as e:
            print("ID GENERATION ERROR:", e)
            return Response(
                {"error": "ID generation failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"status": "Application approved and ID card issued"},
            status=status.HTTP_200_OK,
        )
