from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission

def role_required(allowed_roles):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if request.user.role not in allowed_roles:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'ADMIN'

class IsReviewer(BasePermission):
    def has_permission(self, request, view):
        return request.user.role in ['REVIEWER', 'ADMIN']

class IsApprover(BasePermission):
    def has_permission(self, request, view):
        return request.user.role in ['APPROVER', 'ADMIN']
