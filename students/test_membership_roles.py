from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from .models import School, SchoolMembership, Student


class SchoolMembershipRoleTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.school = School.objects.create(name="Northstar School")
        self.student = Student.objects.create(
            school=self.school,
            name="Asha Sharma",
            total_marks=100,
            marks_obtained=80,
            date=date(2026, 11, 1),
        )
        self.viewer = get_user_model().objects.create_user(
            username="viewer", password="test-password", is_staff=True,
        )
        SchoolMembership.objects.create(
            user=self.viewer,
            school=self.school,
            role=SchoolMembership.Role.VIEWER,
        )

    def test_viewer_can_read_school_data_but_cannot_edit_or_create(self):
        self.client.force_authenticate(user=self.viewer)

        listing = self.client.get("/students/")
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(listing.data["results"][0]["id"], self.student.pk)
        self.assertEqual(self.client.get(f"/students/{self.student.pk}/").status_code, 200)

        update = self.client.patch(
            f"/students/{self.student.pk}/",
            {"marks_obtained": 90},
            format="json",
        )
        create = self.client.post("/students/add/", {
            "name": "Ravi Kumar",
            "total_marks": 100,
            "marks_obtained": 75,
            "date": "2026-11-01",
        }, format="json")

        self.assertEqual(update.status_code, 403)
        self.assertEqual(create.status_code, 403)
        self.student.refresh_from_db()
        self.assertEqual(self.student.marks_obtained, 80)

    def test_manager_role_keeps_write_access(self):
        manager = get_user_model().objects.create_user(
            username="manager", password="test-password", is_staff=True,
        )
        SchoolMembership.objects.create(
            user=manager,
            school=self.school,
            role=SchoolMembership.Role.MANAGER,
        )
        self.client.force_authenticate(user=manager)

        response = self.client.patch(
            f"/students/{self.student.pk}/",
            {"marks_obtained": 90},
            format="json",
        )

        self.assertEqual(response.status_code, 200, response.data)
        self.student.refresh_from_db()
        self.assertEqual(self.student.marks_obtained, 90)
