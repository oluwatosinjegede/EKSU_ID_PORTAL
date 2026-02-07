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


MAX_LEN = 100  # protect varchar(100) fields


def safe(v):
    """Trim + protect DB length"""
    return (v or "").strip()[:MAX_LEN]


class Command(BaseCommand):
    help = "Robust CSV Import (FK-safe, idempotent, duplicate-safe, Railway-safe)"

    def handle(self, *args, **options):

        if os.getenv("IMPORT_STUDENTS") != "true":
            self.stdout.write("IMPORT_STUDENTS not enabled. Skipping.")
            return

        FORCE_REBUILD = os.getenv("REBUILD_STUDENTS") == "true"

        csv_path = Path("students/data/students.csv")

        if not csv_path.exists():
            self.stderr.write(self.style.ERROR("CSV file not found"))
            return

        created = updated = rebuilt = skipped = failed = 0

        with csv_path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)

            for row in reader:

                # ---------- Skip empty ----------
                if not row or all(not c.strip() for c in row):
                    skipped += 1
                    continue

                if len(row) < 6:
                    skipped += 1
                    continue

                # ---------- Clean + truncate ----------
                first_name = safe(row[0])
                middle_name = safe(row[1])
                last_name = safe(row[2])
                matric = safe(row[3])
                department = safe(row[4])
                level = safe(row[5])
                phone = safe(row[6]) if len(row) > 6 else ""

                # Skip header
                if matric.lower() in ("matric_no", "matric", "matric_number"):
                    skipped += 1
                    continue

                try:
                    with transaction.atomic():

                        # ====================================================
                        # USER (Guaranteed unique by username = matric)
                        # ====================================================
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
                            # Sync names if changed
                            changed = False
                            if user.first_name != first_name:
                                user.first_name = first_name
                                changed = True
                            if user.last_name != last_name:
                                user.last_name = last_name
                                changed = True
                            if changed:
                                user.save(update_fields=["first_name", "last_name"])

                        # ====================================================
                        # STUDENT (Prevent duplicate user link)
                        # ====================================================
                        existing_student = Student.objects.filter(user=user).first()

                        if existing_student and existing_student.matric_number != matric:
                            # Another student already linked to this user ? skip
                            skipped += 1
                            continue

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

                    # ====================================================
                    # OPTIONAL ID REBUILD (Safe)
                    # ====================================================
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
