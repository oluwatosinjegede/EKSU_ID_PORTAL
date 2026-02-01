from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import IDApplicationSerializer
from .models import IDApplication
from students.models import Student
from accounts.permissions import IsApprover
from idcards.services import generate_id_card

class ApplyForIDAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        student = Student.objects.get(user=request.user)

        if IDApplication.objects.filter(student=student).exists():
            return Response({'error': 'Application already exists'}, status=400)

        serializer = IDApplicationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(student=student)
        return Response({'status': 'Application submitted'})

class ApproveApplicationAPI(APIView):
    permission_classes = [IsApprover]

    def post(self, request, app_id):
        application = IDApplication.objects.get(id=app_id)
        application.status = 'APPROVED'
        application.reviewed_by = request.user.username
        application.save()

        generate_id_card(application)
        return Response({'status': 'ID card issued'})
