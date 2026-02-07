from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
import os


class Command(BaseCommand):
    help = "Create or repair initial superuser (idempotent, container-safe, login-safe)"

    def handle(self, *args, **options):
        User = get_user_model()

        # -------------------------------------------------
        # READ ENV VARS
        # -------------------------------------------------
        username = os.getenv("DJANGO_ADMIN_USER")
        email = os.getenv("DJANGO_ADMIN_EMAIL")
        password = os.getenv("DJANGO_ADMIN_PASSWORD")

        if not all([username, email, password]):
            self.stdout.write("Admin env vars not fully set. Skipping.")
            return

        try:
            with transaction.atomic():

                # -------------------------------------------------
                # 1. IF SUPERUSER EXISTS ? ENSURE LOGIN WORKS
                # -------------------------------------------------
                existing_superuser = User.objects.filter(is_superuser=True).first()

                if existing_superuser:
                    updated = False

                    if existing_superuser.username != username:
                        existing_superuser.username = username
                        updated = True

                    if existing_superuser.email != email:
                        existing_superuser.email = email
                        updated = True

                    if not existing_superuser.check_password(password):
                        existing_superuser.set_password(password)
                        updated = True

                    if not existing_superuser.is_staff:
                        existing_superuser.is_staff = True
                        updated = True

                    if not existing_superuser.is_active:
                        existing_superuser.is_active = True
                        updated = True

                    if updated:
                        existing_superuser.save()
                        self.stdout.write("Superuser repaired / updated.")
                    else:
                        self.stdout.write("Superuser already valid. Skipping.")

                    return

                # -------------------------------------------------
                # 2. NO SUPERUSER ? CREATE SAFELY
                # -------------------------------------------------
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        "email": email,
                        "is_superuser": True,
                        "is_staff": True,
                        "is_active": True,
                    },
                )

                if created:
                    user.set_password(password)
                    user.save()
                    self.stdout.write(self.style.SUCCESS("Superuser created."))
                    return

                # -------------------------------------------------
                # 3. USER EXISTS BUT NOT SUPERUSER ? PROMOTE
                # -------------------------------------------------
                user.email = email
                user.is_superuser = True
                user.is_staff = True
                user.is_active = True
                user.set_password(password)
                user.save()

                self.stdout.write(self.style.SUCCESS("Existing user promoted to superuser."))

        except Exception as e:
            self.stderr.write(f"Superuser bootstrap failed: {e}")
