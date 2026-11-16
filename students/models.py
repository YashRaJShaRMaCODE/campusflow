from django.conf import settings
from django.db import models
from django.db.models import F, Q


class School(models.Model):
    name = models.CharField(max_length=160)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class StudentChangeEvent(models.Model):
    class Action(models.TextChoices):
        CREATED = "created", "Created"
        UPDATED = "updated", "Updated"

    school = models.ForeignKey(School, on_delete=models.PROTECT, related_name="student_changes")
    student_id = models.PositiveBigIntegerField()
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="campusflow_student_changes",
    )
    action = models.CharField(max_length=8, choices=Action.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-id",)
        indexes = [models.Index(fields=("school", "student_id", "id"), name="student_change_lookup_idx")]


class StudentExportRequest(models.Model):
    school = models.ForeignKey(School, on_delete=models.PROTECT, related_name="student_exports")
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="campusflow_student_exports",
    )
    record_count = models.PositiveIntegerField()
    requested_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-id",)
        indexes = [models.Index(fields=("school", "requested_at"), name="student_export_lookup_idx")]


class SchoolMembership(models.Model):
    class Role(models.TextChoices):
        MANAGER = "manager", "Manager"
        VIEWER = "viewer", "Viewer"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="campusflow_membership",
    )
    school = models.ForeignKey(
        School,
        on_delete=models.PROTECT,
        related_name="memberships",
    )
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.MANAGER)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} — {self.school}"


class Student(models.Model):
    school = models.ForeignKey(
        School,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="students",
    )
    name = models.CharField(max_length=100)
    total_marks = models.PositiveIntegerField()
    marks_obtained = models.PositiveIntegerField()
    date = models.DateField()

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(total_marks__gt=0),
                name="student_total_marks_positive",
            ),
            models.CheckConstraint(
                condition=Q(marks_obtained__lte=F("total_marks")),
                name="student_marks_within_total",
            ),
        ]

    def __str__(self):
        return self.name
