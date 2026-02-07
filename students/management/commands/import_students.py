import csv
import os
from pathlib import Path

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction, IntegrityError

from students.models import Student
from applications.models import IDApplication
from idcards.services import generate_id_card

User = get_user_model()


class Command(BaseCommand):
    help = "Robust Student CSV Import (FK-safe, idempotent, Railway-safe)"

    def handle(self, *args, **options):

        if os.getenv("IMPORT_STUDENTS") != "true":
            self.stdout.write("IMPORT_STUDENTS not enabled. Skipping.")
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
        failed = 0

        # -------- STREAM READ (memory safe) --------
        with csv_path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)

            for row in reader:

                # Skip empty lines
                if not row or all(not c.strip() for c in row):
                    skipped += 1
                    continue

                # Ensure minimum columns
                if len(row) < 6:
                    skipped += 1
                    continue

                first_name = row[0].strip()
                middle_name = row[1].strip()
                last_name = row[2].strip()
                matric = row[3].strip()
                department = row[4].strip()
                level = row[5].strip()
                phone = row[6].strip() if len(row) > 6 else ""

                # Skip header row
                if matric.lower() in ("matric_no", "matric", "matric_number"):
                    skipped += 1
                    continue

                try:
                    with transaction.atomic():

                        # ==============================
                        # CREATE / FIX USER (FK SAFE)
                        # ==============================
                        user, user_created = User.objects.get_or_create(
                            username=matric,
                            defaults={
                                "first_name": first_name,
                                "last_name": last_name,
                                "role": "STUDENT",
                                "must_change_password": True,
                            },
                        )

                        if user_created:
                            user.set_password("ChangeMe123!")
                            user.save()
                        else:
                            # Sync names safely
                            changed = False
                            if user.first_name != first_name:
                                user.first_name = first_name
                                changed = True
                            if user.last_name != last_name:
                                user.last_name = last_name
                                changed = True
                            if changed:
                                user.save(update_fields=["first_name", "last_name"])

                        # ==============================
                        # CREATE / UPDATE STUDENT
                        # ==============================
                        student, created_flag = Student.objects.update_or_create(
                            matric_number=matric,
                            defaults={
                                "user": user,  # <-- FK integrity guaranteed
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

                    # ==============================
                    # OPTIONAL REBUILD ID
                    # ==============================
                    if FORCE_REBUILD:
                        try:
                            app = IDApplication.objects.filter(student=student).first()
                            if app and app.passport:
                                generate_id_card(app)
                                rebuilt += 1
                        except Exception as e:
                            self.stderr.write(f"Rebuild failed for {matric}: {e}")

                except IntegrityError as e:
                    failed += 1
                    self.stderr.write(f"Integrity error for {matric}: {e}")

                except Exception as e:
                    failed += 1
                    self.stderr.write(f"Failed row {matric}: {e}")

        self.stdout.write(
            self.style.SUCCESS(
                f"\nImport complete:\n"
                f"  Created: {created}\n"
                f"  Updated: {updated}\n"
                f"  Rebuilt IDs: {rebuilt}\n"
                f"  Skipped: {skipped}\n"
                f"  Failed: {failed}\n"
            )
        )
