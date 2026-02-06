from django.db import migrations, connection


def add_missing_columns(apps, schema_editor):

    # Skip for SQLite (local dev)
    if connection.vendor != "postgresql":
        return

    table = "students_student"

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = %s
        """, [table])

        existing = {row[0] for row in cursor.fetchall()}

        if "first_name" not in existing:
            cursor.execute(
                "ALTER TABLE students_student ADD COLUMN first_name VARCHAR(100) DEFAULT ''"
            )

        if "middle_name" not in existing:
            cursor.execute(
                "ALTER TABLE students_student ADD COLUMN middle_name VARCHAR(100) DEFAULT ''"
            )

        if "last_name" not in existing:
            cursor.execute(
                "ALTER TABLE students_student ADD COLUMN last_name VARCHAR(100) DEFAULT ''"
            )


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0010_student_created_at_alter_student_department_and_more'),
    ]

    operations = [
        migrations.RunPython(add_missing_columns),
    ]
