from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from .models import School, SchoolMembership, Student


class SchoolSummaryTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="summary-viewer", password="test-password", is_staff=True,
        )
        self.school = School.objects.create(name="Synthetic Demo School")
        SchoolMembership.objects.create(
            user=self.user, school=self.school, role=SchoolMembership.Role.VIEWER,
        )

    def test_summary_is_school_scoped_aggregate_only_and_not_cached(self):
        Student.objects.create(
            school=self.school, name="Synthetic Learner A", total_marks=100,
            marks_obtained=75, date=date(2026, 11, 1),
        )
        Student.objects.create(
            school=self.school, name="Synthetic Learner B", total_marks=100,
            marks_obtained=10, date=date(2026, 11, 1),
        )
        other_school = School.objects.create(name="Other Synthetic School")
        Student.objects.create(
            school=other_school, name="Out of scope", total_marks=100,
            marks_obtained=99, date=date(2026, 11, 1),
        )
        self.client.force_authenticate(user=self.user)

        response = self.client.get("/students/summary/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {
            "student_count": 2,
            "average_marks": 42.5,
            "average_percentage": 42.5,
            "students_above_33_percent": 1,
        })
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertNotIn("Synthetic Learner", str(response.data))

    def test_summary_requires_membership(self):
        self.client.force_authenticate(user=self.user)
        SchoolMembership.objects.filter(user=self.user).delete()

        self.assertEqual(self.client.get("/students/summary/").status_code, 403)
