from django.contrib import admin
from .models import Student
from accounts.admin_mixins import RoleRestrictedAdminMixin


@admin.register(Student)
class StudentAdmin(RoleRestrictedAdminMixin, admin.ModelAdmin):
    allowed_roles = ['ADMIN', 'REVIEWER', 'APPROVER']

    list_display = (
        'matric_number',
        'user',
        'department',
        'level',
        'phone',
    )

    search_fields = (
        'matric_number',
        'user__username',
        'user__first_name',
        'user__middle_name',
        'user__last_name',
    )

    list_filter = ('department', 'level')

