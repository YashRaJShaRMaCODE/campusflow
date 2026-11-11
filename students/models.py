from django.db import models
from django.db.models import F, Q


class Student(models.Model):
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
