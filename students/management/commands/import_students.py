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

        # =========================
        # SAFETY SWITCH (Railway)
        # =========================
        if os.getenv("IMPORT_STUDENTS") != "true":
            self.stdout.write("IMPORT_STUDENTS not enabled. Skipping import.")
            return

        FORCE_REBUILD = os.getenv("REBUILD_STUDENTS") == "true"

        # =========================
        # CSV PATH
        # =========================
        csv_path = Path("students/data/students.csv")

        if not csv_path.exists():
            self.stderr.write(self.style.ERROR("CSV file not found"))
            return

        created = 0
        updated = 0
        rebuilt = 0
        skipped = 0

        with csv_path.open(encoding="utf-8-sig", newline="") as file:

            sample = file.read(2048)
            file.seek(0)

            # =========================
            # Detect delimiter safely
            # =========================
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=";,")
                reader = csv.DictReader(file, dialect=dialect)
            except csv.Error:
                reader = csv.DictReader(file)

            # =========================
            # Fix broken Excel CSV (single column)
            # =========================
            if reader.fieldnames and len(reader.fieldnames) == 1:
                headers = [h.strip() for h in reader.fieldnames[0].split(",")]
                reader.fieldnames = headers

                def fixed_rows():
                    for row in reader:
                        raw = list(row.values())[0]
                        values = [v.strip() for v in raw.split(",")]
                        yield dict(zip(headers, values))

                rows = fixed_rows()
            else:
                rows = reader

            for row in rows:

                matric = (row.get("matric_no") or "").strip()

                # Skip header row wrongly parsed
                if matric.lower() == "matric_no":
                    continue

                if not matric:
                    skipped += 1
                    continue

                first_name = (row.get("first_name") or "").strip()
                middle_name = (row.get("middle_name") or "").strip()
                last_name = (row.get("last_name") or "").strip()
                department = (row.get("department") or "").strip()
                level = (row.get("level") or "").strip()
                phone = (row.get("phone") or "").strip()

                with transaction.atomic():

                    # =========================
                    # Create / Update User
                    # =========================
                    user, user_created = User.objects.get_or_create(
                        username=matric,
                        defaults={
                            "first_name": first_name,
                            "last_name": last_name,
                        },
                    )

                    # Force update names (fix bad imports)
                    if not user_created:
                        user.first_name = first_name
                        user.last_name = last_name
                        user.save(update_fields=["first_name", "last_name"])

                    if user_created:
                        user.set_password("ChangeMe123!")
                        user.save()

                    # =========================
                    # Create / Update Student
                    # =========================
                    student, student_created = Student.objects.update_or_create(
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

                if student_created:
                    created += 1
                else:
                    updated += 1

                # =========================
                # FORCE REBUILD ID CARD
                # =========================
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
