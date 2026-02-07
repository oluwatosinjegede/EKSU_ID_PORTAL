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
    help = "Stable student importer (FK-safe, login-safe, collision-proof, Railway-safe)"

    def handle(self, *args, **options):

        if os.getenv("IMPORT_STUDENTS") != "true":
            self.stdout.write("IMPORT_STUDENTS disabled. Skipping.")
            return

        FORCE_REBUILD = os.getenv("REBUILD_STUDENTS") == "true"

        csv_path = Path("students/data/students.csv")
        if not csv_path.exists():
            self.stderr.write("CSV file not found")
            return

        created = updated = rebuilt = skipped = failed = 0

        with csv_path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)

            for row in reader:

                # -------------------------------------------------
                # BASIC VALIDATION
                # -------------------------------------------------
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

                if matric.lower() in ("matric", "matric_no", "matric_number"):
                    skipped += 1
                    continue

                try:
                    with transaction.atomic():

                        # =================================================
                        # ENSURE USER EXISTS (LOGIN SAFE)
                        # =================================================
                        user, user_created = User.objects.get_or_create(
                            username=matric,
                            defaults={
                                "first_name": first,
                                "last_name": last,
                                "role": "STUDENT",
                                "must_change_password": True,
                            },
                        )

                        if user_created:
                            user.set_password("ChangeMe123!")
                            user.save()
                        else:
                            changed = False
                            if user.first_name != first:
                                user.first_name = first
                                changed = True
                            if user.last_name != last:
                                user.last_name = last
                                changed = True
                            if changed:
                                user.save(update_fields=["first_name", "last_name"])

                        # =================================================
                        # HARD COLLISION PROTECTION (OneToOne safe)
                        # =================================================
                        existing_owner = Student.objects.filter(user=user).first()

                        if existing_owner and existing_owner.matric_number != matric:
                            # Create guaranteed unique username
                            suffix = 1
                            new_username = matric

                            while User.objects.filter(username=new_username).exists():
                                suffix += 1
                                new_username = f"{matric}_{suffix}"

                            user = User.objects.create(
                                username=new_username,
                                first_name=first,
                                last_name=last,
                                role="STUDENT",
                                must_change_password=True,
                            )
                            user.set_password("ChangeMe123!")
                            user.save()

                        # =================================================
                        # CREATE / UPDATE STUDENT (FK SAFE)
                        # =================================================
                        student, created_flag = Student.objects.update_or_create(
                            matric_number=matric,
                            defaults={
                                "user": user,
                                "first_name": first,
                                "middle_name": middle,
                                "last_name": last,
                                "department": dept,
                                "level": level,
                                "phone": phone,
                            },
                        )

                    if created_flag:
                        created += 1
                    else:
                        updated += 1

                    # =================================================
                    # OPTIONAL ID REBUILD
                    # =================================================
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
                    self.stderr.write(f"Integrity error {matric}: {e}")

                except Exception as e:
                    failed += 1
                    self.stderr.write(f"Failed {matric}: {e}")

        self.stdout.write(
            self.style.SUCCESS(
                f"""
Import complete:
  Created: {created}
  Updated: {updated}
  Rebuilt IDs: {rebuilt}
  Skipped: {skipped}
  Failed: {failed}
"""
            )
        )
