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
    help = "Self-healing student importer (fully hardened, FK-safe, idempotent, zero-crash)"

    def handle(self, *args, **options):

        if os.getenv("IMPORT_STUDENTS") != "true":
            self.stdout.write("IMPORT_STUDENTS disabled. Skipping.")
            return

        FORCE_REBUILD = os.getenv("REBUILD_STUDENTS") == "true"
        DRY_RUN = os.getenv("DRY_RUN_IMPORT") == "true"

        csv_path = Path("students/data/students.csv")
        if not csv_path.exists():
            self.stderr.write("CSV file not found")
            return

        created = updated = healed_users = healed_students = rebuilt = skipped = failed = 0

        # -------------------------------------------------
        # CSV SANITIZER (fix broken quotes / encoding)
        # -------------------------------------------------
        with csv_path.open(encoding="utf-8-sig", newline="") as f:

            clean_lines = (
                line.replace('"', '').strip()
                for line in f
                if line.strip()
            )

            reader = csv.reader(clean_lines)

            for row in reader:

                if not row or len(row) < 6:
                    skipped += 1
                    continue

                first = row[0].strip()[:50]
                middle = row[1].strip()[:50]
                last = row[2].strip()[:50]
                matric = row[3].strip().upper()
                dept = row[4].strip()[:100]
                level = row[5].strip()[:10]
                phone = row[6].strip()[:20] if len(row) > 6 else ""

                if not matric or matric.lower() in ("matric", "matric_no", "matric_number"):
                    skipped += 1
                    continue

                try:
                    with transaction.atomic():

                        # -------------------------------------------------
                        # 1. FIND STUDENT BY MATRIC
                        # -------------------------------------------------
                        student = Student.objects.filter(matric_number=matric).first()
                        user = None

                        if student:
                            # -------------------------------------------------
                            # REPAIR BROKEN FK (student.user missing)
                            # -------------------------------------------------
                            if not student.user_id:
                                user = User.objects.create(
                                    username=matric,
                                    first_name=first,
                                    last_name=last,
                                    role="STUDENT",
                                    must_change_password=True,
                                )
                                user.set_password("ChangeMe123!")
                                user.save()

                                student.user = user
                                student.save(update_fields=["user"])
                                healed_students += 1

                            else:
                                try:
                                    user = student.user
                                except User.DoesNotExist:
                                    # Heal orphan student
                                    user = User.objects.create(
                                        username=matric,
                                        first_name=first,
                                        last_name=last,
                                        role="STUDENT",
                                        must_change_password=True,
                                    )
                                    user.set_password("ChangeMe123!")
                                    user.save()

                                    student.user = user
                                    student.save(update_fields=["user"])
                                    healed_students += 1

                        # -------------------------------------------------
                        # 2. ENSURE USER EXISTS
                        # -------------------------------------------------
                        if not user:
                            user = User.objects.filter(username=matric).first()

                            if not user:
                                user = User.objects.create(
                                    username=matric,
                                    first_name=first,
                                    last_name=last,
                                    role="STUDENT",
                                    must_change_password=True,
                                )
                                user.set_password("ChangeMe123!")
                                user.save()
                            else:
                                healed_users += 1

                        # -------------------------------------------------
                        # 3. ONE-TO-ONE SAFETY
                        # -------------------------------------------------
                        owner = Student.objects.filter(user=user).first()
                        if owner and owner.matric_number != matric:
                            student = owner

                        # -------------------------------------------------
                        # 4. CREATE OR UPDATE STUDENT
                        # -------------------------------------------------
                        if not student:
                            if not DRY_RUN:
                                student = Student.objects.create(
                                    user=user,
                                    matric_number=matric,
                                    first_name=first,
                                    middle_name=middle,
                                    last_name=last,
                                    department=dept,
                                    level=level,
                                    phone=phone,
                                )
                            created += 1
                        else:
                            if not DRY_RUN:
                                Student.objects.filter(id=student.id).update(
                                    first_name=first,
                                    middle_name=middle,
                                    last_name=last,
                                    department=dept,
                                    level=level,
                                    phone=phone,
                                )
                            updated += 1

                    # -------------------------------------------------
                    # 5. OPTIONAL ID REBUILD
                    # -------------------------------------------------
                    if FORCE_REBUILD and student:
                        try:
                            app = IDApplication.objects.filter(student=student).first()
                            if app and app.passport:
                                if not DRY_RUN:
                                    generate_id_card(app)
                                rebuilt += 1
                        except Exception:
                            pass

                except IntegrityError as e:
                    failed += 1
                    self.stderr.write(f"INTEGRITY ERROR {matric}: {repr(e)}")
                    continue

                except Exception as e:
                    failed += 1
                    self.stderr.write(f"FAILED {matric}: {repr(e)}")
                    continue

        self.stdout.write(
            self.style.SUCCESS(
                f"""
SELF-HEAL IMPORT COMPLETE

Created: {created}
Updated: {updated}
Healed Students (missing user): {healed_students}
Healed Users (missing student): {healed_users}
Rebuilt IDs: {rebuilt}
Skipped: {skipped}
Failed: {failed}
"""
            )
        )
