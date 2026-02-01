import csv
from pathlib import Path

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

from students.models import Student

User = get_user_model()


class Command(BaseCommand):
    help = "Import students from CSV file"

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_file",
            type=str,
            help="Absolute or relative path to CSV file",
        )

    def handle(self, *args, **options):
        csv_path = Path(options["csv_file"])

        if not csv_path.exists():
            self.stderr.write(self.style.ERROR("❌ CSV file not found"))
            return

        created = 0
        updated = 0
        skipped = 0

        with csv_path.open(encoding="utf-8-sig", newline="") as file:
            sample = file.read(2048)
            file.seek(0)

            # Detect delimiter safely
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=";,")
                reader = csv.DictReader(file, dialect=dialect)
            except csv.Error:
                reader = csv.DictReader(file)

            # 🔥 Fix Excel single-column CSV issue
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
                matric_number = (
                    row.get("matric_no")
                    or row.get("matric_number")
                    or ""
                ).strip()

                if not matric_number:
                    skipped += 1
                    continue

                with transaction.atomic():
                    user, user_created = User.objects.get_or_create(
                        username=matric_number,
                        defaults={
                            "first_name": row.get("first_name", "").strip(),
                            "last_name": row.get("last_name", "").strip(),
                            "email": row.get("email", "").strip(),
                        },
                    )

                    if user_created:
                        user.set_password("ChangeMe123!")  # force reset
                        user.save()

                    student, student_created = Student.objects.update_or_create(
                        matric_number=matric_number,
                        defaults={
                            "user": user,
                            "middle_name": row.get("middle_name", "").strip(),
                            "department": row.get("department", "").strip(),
                            "level": row.get("level", "100").strip(),
                            "phone": row.get("phone", "").strip(),
                        },
                    )

                if student_created:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Import complete: {created} created, {updated} updated, {skipped} skipped"
            )
        )
