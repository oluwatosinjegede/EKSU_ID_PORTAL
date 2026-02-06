from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0012_alter_student_created_at'),  # keep your last successful migration here
    ]

    operations = [
        migrations.RunSQL(
            """
            ALTER TABLE students_student ALTER COLUMN first_name TYPE varchar(100);
            ALTER TABLE students_student ALTER COLUMN middle_name TYPE varchar(100);
            ALTER TABLE students_student ALTER COLUMN last_name TYPE varchar(100);
            ALTER TABLE students_student ALTER COLUMN department TYPE varchar(150);
            ALTER TABLE students_student ALTER COLUMN level TYPE varchar(50);
            ALTER TABLE students_student ALTER COLUMN matric_number TYPE varchar(50);
            """,
            reverse_sql=migrations.RunSQL.noop
        )
    ]
