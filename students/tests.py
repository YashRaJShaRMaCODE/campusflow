from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Student


class StudentApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="staff", password="test-password", is_staff=True,
        )

    def authenticate(self):
        self.client.force_authenticate(user=self.user)

    def test_api_root_lists_safe_endpoint_urls(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "Student Records API")
        self.assertIn("health", response.data["endpoints"])
        self.assertIn("sign_in", response.data["endpoints"])

    def test_health_is_public_and_returns_minimal_status(self):
        response = self.client.get("/healthz/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_student_data_requires_authentication(self):
        for path in ("/students/", "/students/1/", "/students/average/", "/students/count/"):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 403)
        self.assertEqual(self.client.post("/students/add/", {}).status_code, 403)

    def test_student_data_rejects_authenticated_non_staff_users(self):
        user = get_user_model().objects.create_user(username="student", password="test-password")
        self.client.force_authenticate(user=user)
        for path in ("/students/", "/students/1/", "/students/average/", "/students/count/"):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 403)
        self.assertEqual(self.client.post("/students/add/", {}).status_code, 403)

    def test_create_validates_marks_and_normalizes_name(self):
        self.authenticate()
        invalid = self.client.post("/students/add/", {
            "name": "Asha", "total_marks": 50, "marks_obtained": 51, "date": "2026-11-01",
        }, format="json")
        self.assertEqual(invalid.status_code, 400)

        valid = self.client.post("/students/add/", {
            "name": "  Asha Sharma  ", "total_marks": 50, "marks_obtained": 33, "date": "2026-11-01",
        }, format="json")
        self.assertEqual(valid.status_code, 201)
        self.assertEqual(valid.data["name"], "Asha Sharma")

        zero_total = self.client.post("/students/add/", {
            "name": "Invalid", "total_marks": 0, "marks_obtained": 0, "date": "2026-11-01",
        }, format="json")
        self.assertEqual(zero_total.status_code, 400)

    def test_list_is_paginated_searchable_and_orderable(self):
        self.authenticate()
        Student.objects.bulk_create([
            Student(name=f"Student {index:02d}", total_marks=100, marks_obtained=index, date=date(2026, 11, 1))
            for index in range(30)
        ])

        first = self.client.get("/students/?page_size=10&ordering=name")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.data["count"], 30)
        self.assertEqual(len(first.data["results"]), 10)
        self.assertIsNotNone(first.data["next"])

        search = self.client.get("/students/?search=Student%2029")
        self.assertEqual(search.data["count"], 1)
        self.assertEqual(search.data["results"][0]["name"], "Student 29")

    def test_list_filters_by_date_and_percentage_and_reports_percentage(self):
        self.authenticate()
        Student.objects.bulk_create([
            Student(name="Outside range", total_marks=100, marks_obtained=95, date=date(2026, 10, 31)),
            Student(name="Below range", total_marks=100, marks_obtained=70, date=date(2026, 11, 2)),
            Student(name="In range", total_marks=200, marks_obtained=170, date=date(2026, 11, 3)),
        ])

        response = self.client.get(
            "/students/?date_from=2026-11-01&date_to=2026-11-05&min_percentage=80&max_percentage=90"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "In range")
        self.assertEqual(response.data["results"][0]["percentage"], 85)

    def test_list_rejects_invalid_date_and_percentage_filters(self):
        self.authenticate()
        for query in (
            "?date_from=not-a-date",
            "?date_from=2026-11-05&date_to=2026-11-01",
            "?min_percentage=101",
            "?min_percentage=80&max_percentage=70",
        ):
            with self.subTest(query=query):
                self.assertEqual(self.client.get(f"/students/{query}").status_code, 400)

    def test_staff_can_read_and_correct_a_record_without_violating_marks(self):
        self.authenticate()
        student = Student.objects.create(
            name="Existing record", total_marks=50, marks_obtained=33, date=date(2026, 11, 1),
        )

        detail = self.client.get(f"/students/{student.pk}/")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.data["percentage"], 66)

        invalid = self.client.patch(f"/students/{student.pk}/", {"total_marks": 30}, format="json")
        self.assertEqual(invalid.status_code, 400)
        student.refresh_from_db()
        self.assertEqual(student.total_marks, 50)

        updated = self.client.patch(f"/students/{student.pk}/", {"marks_obtained": 25}, format="json")
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.data["percentage"], 50)

    def test_aggregates_are_correct_for_empty_and_populated_data(self):
        self.authenticate()
        empty = self.client.get("/students/average/")
        self.assertEqual(empty.data, {"student_count": 0, "average_marks": 0, "average_percentage": 0})
        self.assertEqual(self.client.get("/students/count/").data["students_above_33_percent"], 0)

        Student.objects.bulk_create([
            Student(name="Asha", total_marks=100, marks_obtained=33, date=date(2026, 11, 1)),
            Student(name="Dev", total_marks=50, marks_obtained=25, date=date(2026, 11, 1)),
        ])
        stats = self.client.get("/students/average/")
        self.assertEqual(stats.data, {"student_count": 2, "average_marks": 29, "average_percentage": 38.67})
        self.assertEqual(self.client.get("/students/count/").data["students_above_33_percent"], 2)
