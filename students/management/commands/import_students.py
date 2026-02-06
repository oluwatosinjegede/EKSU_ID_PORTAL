import csv
import os
from pathlib import Path

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

from students.models import Student
from applications.models import IDApplication
from idcards.services import generate_id_card

User = get_user_model()


class Command(BaseCommand):
    help = "Import students from CSV (robust, Railway-safe, rebuild capable)"

    def handle(self, *args, **options):

        if os.getenv("IMPORT_STUDENTS") != "true":
            self.stdout.write("IMPORT_STUDENTS not enabled. Skipping import.")
            return

        FORCE_REBUILD = os.getenv("REBUILD_STUDENTS") == "true"

        csv_path = Path("students/data/students.csv")

        if not csv_path.exists():
            self.stderr.write(self.style.ERROR("CSV file not found"))
            return

        created = updated = rebuilt = skipped = 0

        with csv_path.open(encoding="utf-8-sig") as file:

            for raw in file:

                raw = raw.strip()

                if not raw:
                    skipped += 1
                    continue

                # Split safely (handles broken Excel)
                parts = [p.strip() for p in raw.split(",") if p.strip() != ""]

                # Must have at least 6 values
                if len(parts) < 6:
                    skipped += 1
                    continue

                first_name = parts[0]
                middle_name = parts[1]
                last_name = parts[2]
                matric = parts[3]
                department = parts[4]
                level = parts[5]
                phone = parts[6] if len(parts) > 6 else ""

                # Skip header row
                if matric.lower() in ("matric_no", "matric", "matric_number"):
                    skipped += 1
                    continue

                with transaction.atomic():

                    user, user_created = User.objects.get_or_create(
                        username=matric,
                        defaults={
                            "first_name": first_name,
                            "last_name": last_name,
                        },
                    )

                    if user_created:
                        user.set_password("ChangeMe123!")
                        user.save()
                    else:
                        user.first_name = first_name
                        user.last_name = last_name
                        user.save(update_fields=["first_name", "last_name"])

                    student, created_flag = Student.objects.update_or_create(
                        matric_number=matric,
                        defaults={
                            "user": user,
                            "first_name": first_name,
                            "middle_name": middle_name,
                            "last_name": last_name,
                            "department": department,
                            "level": level,
                            "phone": phone,
                        },
                    )

                if created_flag:
                    created += 1
                else:
                    updated += 1

                if FORCE_REBUILD:
                    try:
                        app = IDApplication.objects.filter(student=student).first()
                        if app:
                            generate_id_card(app)
                            rebuilt += 1
                    except Exception as e:
                        print(f"Rebuild failed for {matric}: {e}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Import complete: {created} created, {updated} updated, "
                f"{rebuilt} ID rebuilt, {skipped} skipped"
            )
        )
