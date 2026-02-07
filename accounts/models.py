from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = (
        ("STUDENT", "Student"),
        ("REVIEWER", "Reviewer"),
        ("APPROVER", "Approver"),
        ("ADMIN", "Administrator"),
    )

    # =========================
    # CORE FIELDS
    # =========================
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="STUDENT",
        db_index=True,
    )

    must_change_password = models.BooleanField(default=True)

    # =========================
    # FIX reverse accessor clashes
    # =========================
    groups = models.ManyToManyField(
        "auth.Group",
        related_name="accounts_user_set",
        blank=True,
    )

    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="accounts_user_permissions_set",
        blank=True,
    )

    # =========================
    # HELPERS
    # =========================
    @property
    def can_access_admin(self):
        return self.role in ["REVIEWER", "APPROVER", "ADMIN"]

    @property
    def is_student(self):
        return self.role == "STUDENT"

    @property
    def is_reviewer(self):
        return self.role == "REVIEWER"

    @property
    def is_approver(self):
        return self.role == "APPROVER"

    @property
    def is_admin_role(self):
        return self.role == "ADMIN"

    def __str__(self):
        return f"{self.username} ({self.role})"
