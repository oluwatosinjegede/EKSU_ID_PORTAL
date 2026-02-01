from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import IDApplication
from students.models import Student

@login_required
def apply_for_id(request):
    student = Student.objects.get(user=request.user)

    if request.method == 'POST':
        IDApplication.objects.create(
            student=student,
            passport=request.FILES['passport'],
            signature=request.FILES['signature']
        )
        return redirect('dashboard')

    return render(request, 'apply.html')

@login_required
def approve_id(request, app_id):
    application = IDApplication.objects.get(id=app_id)

    application.status = 'APPROVED'
    application.reviewed_by = request.user.username
    application.save()

    from idcards.utils import generate_id_card
    generate_id_card(application)

    return redirect('admin_dashboard')
