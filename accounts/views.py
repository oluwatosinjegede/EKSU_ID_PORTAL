from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from students.models import Student
from applications.models import IDApplication
from idcards.models import IDCard

from django.contrib.auth import update_session_auth_hash


def home_view(request):
    return render(request, 'home.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)

            if getattr(user, 'must_change_password', False):
                return redirect('force-change-password')
            
            if hasattr(user, 'student'):
                return redirect('student-dashboard')

            return redirect('/admin/')

        return render(request, 'auth/login.html', {
            'error': 'Invalid login credentials'
        })

    return render(request, 'auth/login.html')


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
@login_required
def student_dashboard(request):
    student = Student.objects.get(user=request.user)
    application = IDApplication.objects.filter(student=student).first()
    id_card = IDCard.objects.filter(student=student).first()

    timeline = {
        'applied': application is not None,
        'review': application is not None and application.status == 'PENDING',
        'approved': application is not None and application.status == 'APPROVED',
        'issued': id_card is not None,
    }

    return render(request, 'student/dashboard.html', {
        'student': student,
        'application': application,
        'id_card': id_card,
        'timeline': timeline,
    })


@login_required
def apply_id_view(request):
    student = Student.objects.get(user=request.user)

    if IDApplication.objects.filter(student=student).exists():
        return redirect('student-dashboard')

    if request.method == 'POST':
        passport = request.FILES['passport']
        signature = request.FILES['signature']

        IDApplication.objects.create(
            student=student,
            passport=passport,
            signature=signature,
        )

        return redirect('student-dashboard')

    return render(request, 'student/apply_id.html')



@login_required
def force_change_password_view(request):
    user = request.user

    if not getattr(user, 'must_change_password', False):
        return redirect('student-dashboard')

    if request.method == 'POST':
        p1 = request.POST.get('password1')
        p2 = request.POST.get('password2')

        if not p1 or not p2:
            return render(request, 'auth/force_change_password.html', {
                'error': 'All fields are required'
            })

        if p1 != p2:
            return render(request, 'auth/force_change_password.html', {
                'error': 'Passwords do not match'
            })

        if len(p1) < 8:
            return render(request, 'auth/force_change_password.html', {
                'error': 'Password must be at least 8 characters long'
            })

        user.set_password(p1)
        user.must_change_password = False
        user.save()

        update_session_auth_hash(request, user)

        return redirect('student-dashboard')

    return render(request, 'auth/force_change_password.html')
