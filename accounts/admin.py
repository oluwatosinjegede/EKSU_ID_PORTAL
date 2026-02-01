from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User as AuthUser

# 🔴 CRITICAL: remove Django's default User admin registration
admin.site.unregister(AuthUser)

# Get the custom user model
User = get_user_model()


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
