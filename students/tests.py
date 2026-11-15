import csv
from datetime import date
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from rest_framework.test import APIClient

from .models import School, SchoolMembership, Student, StudentChangeEvent, StudentExportRequest


class StudentApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="staff", password="test-password", is_staff=True,
        )
        self.school = School.objects.create(name="Northstar School")
        SchoolMembership.objects.create(user=self.user, school=self.school)

    def authenticate(self):
        self.client.force_authenticate(user=self.user)

    def test_api_root_lists_safe_endpoint_urls(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "CampusFlow API")
        self.assertIn("health", response.data["endpoints"])
        self.assertIn("export_csv", response.data["endpoints"])
        self.assertIn("sign_in", response.data["endpoints"])

    def test_health_is_public_and_returns_minimal_status(self):
        response = self.client.get("/healthz/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_student_data_requires_authentication(self):
        paths = (
            "/students/", "/students/export.csv", "/students/exports/", "/students/1/",
            "/students/1/changes/", "/students/average/", "/students/count/",
        )
        for path in paths:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 403)
        self.assertEqual(self.client.post("/students/add/", {}).status_code, 403)

    def test_private_student_responses_are_never_cached(self):
        student = Student.objects.create(
            school=self.school, name="Private record", total_marks=100,
            marks_obtained=80, date=date(2026, 11, 1),
        )
        self.authenticate()
        for path in (
            "/students/", "/students/exports/", f"/students/{student.pk}/",
            f"/students/{student.pk}/changes/", "/students/average/", "/students/count/",
        ):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response["Cache-Control"], "private, no-store")

    def test_student_data_rejects_authenticated_non_staff_users(self):
        user = get_user_model().objects.create_user(username="student", password="test-password")
        self.client.force_authenticate(user=user)
        paths = (
            "/students/", "/students/export.csv", "/students/exports/", "/students/1/",
            "/students/1/changes/", "/students/average/", "/students/count/",
        )
        for path in paths:
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
        student = Student.objects.get(pk=valid.data["id"])
        self.assertEqual(student.school, self.school)
        self.assertEqual(StudentChangeEvent.objects.filter(student_id=student.pk).count(), 1)
        history = self.client.get(f"/students/{student.pk}/changes/")
        self.assertEqual(history.status_code, 200)
        self.assertEqual(history.data["results"][0]["action"], "created")
        self.assertNotIn("name", history.data["results"][0])

        zero_total = self.client.post("/students/add/", {
            "name": "Invalid", "total_marks": 0, "marks_obtained": 0, "date": "2026-11-01",
        }, format="json")
        self.assertEqual(zero_total.status_code, 400)

    def test_list_is_paginated_searchable_and_orderable(self):
        self.authenticate()
        Student.objects.bulk_create([
            Student(
                school=self.school,
                name=f"Student {index:02d}",
                total_marks=100,
                marks_obtained=index,
                date=date(2026, 11, 1),
            )
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
            Student(
                school=self.school, name="Outside range", total_marks=100,
                marks_obtained=95, date=date(2026, 10, 31),
            ),
            Student(school=self.school, name="Below range", total_marks=100, marks_obtained=70, date=date(2026, 11, 2)),
            Student(school=self.school, name="In range", total_marks=200, marks_obtained=170, date=date(2026, 11, 3)),
        ])

        response = self.client.get(
            "/students/?date_from=2026-11-01&date_to=2026-11-05&min_percentage=80&max_percentage=90"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "In range")
        self.assertEqual(response.data["results"][0]["percentage"], 85)

    def test_csv_export_is_filtered_school_scoped_and_formula_safe(self):
        other_school = School.objects.create(name="Other School")
        Student.objects.create(
            school=self.school, name="=SUM(1,2)", total_marks=100,
            marks_obtained=90, date=date(2026, 11, 3),
        )
        Student.objects.create(
            school=self.school, name="Below threshold", total_marks=100,
            marks_obtained=70, date=date(2026, 11, 3),
        )
        Student.objects.create(
            school=other_school, name="Hidden student", total_marks=100,
            marks_obtained=95, date=date(2026, 11, 3),
        )
        self.authenticate()

        response = self.client.get("/students/export.csv?min_percentage=80")
        content = b"".join(response.streaming_content).decode("utf-8-sig")
        rows = list(csv.reader(StringIO(content)))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn("no-store", response["Cache-Control"])
        self.assertIn("attachment;", response["Content-Disposition"])
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1][1], "'=SUM(1,2)")
        self.assertNotIn("Hidden student", content)
        self.assertNotIn("Below threshold", content)
        audit = StudentExportRequest.objects.get()
        self.assertEqual(audit.school, self.school)
        self.assertEqual(audit.actor, self.user)
        self.assertEqual(audit.record_count, 1)

        other_user = get_user_model().objects.create_user(
            username="other-staff", password="test-password", is_staff=True,
        )
        SchoolMembership.objects.create(user=other_user, school=other_school)
        StudentExportRequest.objects.create(school=other_school, actor=other_user, record_count=99)
        history = self.client.get("/students/exports/")
        self.assertEqual(history.data["count"], 1)
        self.assertEqual(history.data["results"][0]["actor_id"], self.user.pk)
        self.assertEqual(history.data["results"][0]["record_count"], 1)
        self.assertNotIn("name", history.data["results"][0])

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
            school=self.school, name="Existing record", total_marks=50, marks_obtained=33, date=date(2026, 11, 1),
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
        history = self.client.get(f"/students/{student.pk}/changes/")
        self.assertEqual(history.status_code, 200)
        self.assertEqual([item["action"] for item in history.data["results"]], ["updated"])
        self.assertEqual(history.data["results"][0]["actor_id"], self.user.pk)
        self.assertNotIn("name", history.data["results"][0])
        self.assertNotIn("marks_obtained", history.data["results"][0])

    def test_change_history_is_scoped_to_school(self):
        other_school = School.objects.create(name="Other School")
        other_student = Student.objects.create(
            school=other_school, name="Private record", total_marks=100,
            marks_obtained=75, date=date(2026, 11, 1),
        )
        self.authenticate()
        self.assertEqual(self.client.get(f"/students/{other_student.pk}/changes/").status_code, 404)

    def test_student_create_rolls_back_if_change_event_cannot_be_written(self):
        self.authenticate()
        with patch("students.views.StudentChangeEvent.objects.create", side_effect=IntegrityError):
            with self.assertRaises(IntegrityError):
                self.client.post("/students/add/", {
                    "name": "Asha", "total_marks": 100, "marks_obtained": 82,
                    "date": "2026-11-01",
                }, format="json")

        self.assertFalse(Student.objects.exists())

    def test_aggregates_are_correct_for_empty_and_populated_data(self):
        self.authenticate()
        empty = self.client.get("/students/average/")
        self.assertEqual(empty.data, {"student_count": 0, "average_marks": 0, "average_percentage": 0})
        self.assertEqual(self.client.get("/students/count/").data["students_above_33_percent"], 0)

        Student.objects.bulk_create([
            Student(school=self.school, name="Asha", total_marks=100, marks_obtained=33, date=date(2026, 11, 1)),
            Student(school=self.school, name="Dev", total_marks=50, marks_obtained=25, date=date(2026, 11, 1)),
        ])
        stats = self.client.get("/students/average/")
        self.assertEqual(stats.data, {"student_count": 2, "average_marks": 29, "average_percentage": 38.67})
        self.assertEqual(self.client.get("/students/count/").data["students_above_33_percent"], 2)

    def test_school_membership_scopes_lists_details_and_summaries(self):
        another_school = School.objects.create(name="Southridge School")
        another_user = get_user_model().objects.create_user(
            username="southridge-staff", password="test-password", is_staff=True,
        )
        SchoolMembership.objects.create(user=another_user, school=another_school)
        own_student = Student.objects.create(
            school=self.school, name="North Student", total_marks=100,
            marks_obtained=80, date=date(2026, 11, 1),
        )
        other_student = Student.objects.create(
            school=another_school, name="South Student", total_marks=100,
            marks_obtained=90, date=date(2026, 11, 1),
        )

        self.authenticate()
        listing = self.client.get("/students/")
        self.assertEqual(listing.data["count"], 1)
        self.assertEqual(listing.data["results"][0]["id"], own_student.pk)
        self.assertEqual(self.client.get(f"/students/{other_student.pk}/").status_code, 404)
        self.assertEqual(self.client.get("/students/average/").data["student_count"], 1)
        self.assertEqual(self.client.get("/students/count/").data["students_above_33_percent"], 1)

        self.client.force_authenticate(user=another_user)
        other_listing = self.client.get("/students/")
        self.assertEqual(other_listing.data["count"], 1)
        self.assertEqual(other_listing.data["results"][0]["id"], other_student.pk)

    def test_staff_without_school_membership_cannot_access_student_data(self):
        staff = get_user_model().objects.create_user(
            username="unassigned-staff", password="test-password", is_staff=True,
        )
        self.client.force_authenticate(user=staff)

        for path in ("/students/", "/students/average/", "/students/count/"):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 403)
        self.assertEqual(self.client.post("/students/add/", {}).status_code, 403)
