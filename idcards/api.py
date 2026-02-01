from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import IDCard
from students.models import Student

class MyIDCardAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        student = Student.objects.get(user=request.user)
        card = IDCard.objects.get(student=student)
        return Response({'download_url': card.pdf.url})

class VerifyIDCardAPI(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, uid):
        try:
            card = IDCard.objects.get(uid=uid, is_active=True)
            return Response({
                'valid': True,
                'student': card.student.matric_number,
                'department': card.student.department
            })
        except IDCard.DoesNotExist:
            return Response({'valid': False}, status=404)
