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
    help = "Import students from CSV (Railway-safe, FORCE rebuild capable)"

    def handle(self, *args, **options):

        # ----------------------------
        # SAFETY SWITCH
        # ----------------------------
        if os.getenv("IMPORT_STUDENTS") != "true":
            self.stdout.write("IMPORT_STUDENTS not enabled. Skipping import.")
            return

        FORCE_REBUILD = os.getenv("REBUILD_STUDENTS") == "true"

        csv_path = Path("students/data/students.csv")

        if not csv_path.exists():
            self.stderr.write(self.style.ERROR("CSV file not found"))
            return

        created = 0
        updated = 0
        rebuilt = 0
        skipped = 0

        with csv_path.open(encoding="utf-8-sig", newline="") as file:

            raw_reader = csv.reader(file)

            for raw_row in raw_reader:

                if not raw_row:
                    skipped += 1
                    continue

                # ----------------------------
                # Handle BROKEN Excel CSV (single column)
                # ----------------------------
                if len(raw_row) == 1:
                    raw_row = raw_row[0].split(",")

                row = [v.strip() for v in raw_row]

                if len(row) < 6:
                    skipped += 1
                    continue

                # Safe unpack (phone optional)
                first_name = row[0] if len(row) > 0 else ""
                middle_name = row[1] if len(row) > 1 else ""
                last_name = row[2] if len(row) > 2 else ""
                matric = row[3] if len(row) > 3 else ""
                department = row[4] if len(row) > 4 else ""
                level = row[5] if len(row) > 5 else ""
                phone = row[6] if len(row) > 6 else ""

                # ----------------------------
                # Skip header / bad rows
                # ----------------------------
                if not matric or matric.lower() in ("matric_no", "matric"):
                    skipped += 1
                    continue

                with transaction.atomic():

                    # ---------------- USER ----------------
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

                    # ---------------- STUDENT ----------------
                    student, created_flag = Student.objects.update_or_create(
                        matric_no=matric,
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

                # ---------------- FORCE ID REBUILD ----------------
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
