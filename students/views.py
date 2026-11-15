import csv
import math

from django.db import transaction
from django.db.models import Avg, Count, ExpressionWrapper, F, FloatField, Sum
from django.http import JsonResponse, StreamingHttpResponse
from django.urls import reverse
from django.utils.dateparse import parse_date
from rest_framework import filters, generics
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Student, StudentChangeEvent, StudentExportRequest
from .permissions import HasSchoolMembership
from .serializers import StudentChangeEventSerializer, StudentExportRequestSerializer, StudentSerializer


class PrivateStudentDataMixin:
    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Cache-Control"] = "private, no-store"
        return response


class StudentCreateView(PrivateStudentDataMixin, generics.CreateAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAdminUser, HasSchoolMembership]

    def perform_create(self, serializer):
        with transaction.atomic():
            student = serializer.save(school=self.request.school)
            StudentChangeEvent.objects.create(
                school=self.request.school,
                student_id=student.pk,
                actor=self.request.user,
                action=StudentChangeEvent.Action.CREATED,
            )


class StudentPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 100


class StudentListView(PrivateStudentDataMixin, generics.ListAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAdminUser, HasSchoolMembership]
    pagination_class = StudentPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["name", "date", "marks_obtained", "total_marks"]
    ordering = ["-date", "name", "id"]

    def get_queryset(self):
        queryset = Student.objects.filter(school=self.request.school)
        params = self.request.query_params

        date_from = self._date_filter(params.get("date_from"), "date_from")
        date_to = self._date_filter(params.get("date_to"), "date_to")
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        if date_from and date_to and date_from > date_to:
            raise ValidationError({"date_to": "Must be the same as or later than date_from."})

        minimum = self._percentage_filter(params.get("min_percentage"), "min_percentage")
        maximum = self._percentage_filter(params.get("max_percentage"), "max_percentage")
        if minimum is not None and maximum is not None and minimum > maximum:
            raise ValidationError({"max_percentage": "Must be greater than or equal to min_percentage."})
        if minimum is not None or maximum is not None:
            percentage = ExpressionWrapper(
                F("marks_obtained") * 100.0 / F("total_marks"),
                output_field=FloatField(),
            )
            queryset = queryset.annotate(percentage=percentage)
            if minimum is not None:
                queryset = queryset.filter(percentage__gte=minimum)
            if maximum is not None:
                queryset = queryset.filter(percentage__lte=maximum)
        return queryset

    @staticmethod
    def _date_filter(value, field):
        if value is None or value == "":
            return None
        parsed = parse_date(value)
        if parsed is None:
            raise ValidationError({field: "Use a valid date in YYYY-MM-DD format."})
        return parsed

    @staticmethod
    def _percentage_filter(value, field):
        if value is None or value == "":
            return None
        try:
            parsed = float(value)
        except ValueError:
            parsed = math.nan
        if not math.isfinite(parsed) or not 0 <= parsed <= 100:
            raise ValidationError({field: "Use a number from 0 to 100."})
        return parsed


class _CsvEcho:
    def write(self, value):
        return value


class StudentCsvExportView(StudentListView):
    def get(self, request):
        writer = csv.writer(_CsvEcho())
        queryset = self.filter_queryset(self.get_queryset()).values_list(
            "id", "name", "date", "marks_obtained", "total_marks",
        )
        StudentExportRequest.objects.create(
            school=request.school,
            actor=request.user,
            record_count=queryset.count(),
        )

        def rows():
            yield writer.writerow(("student_id", "name", "date", "marks_obtained", "total_marks", "percentage"))
            for student_id, name, exam_date, marks, total in queryset.iterator(chunk_size=500):
                safe_name = f"'{name}" if name.lstrip(" \t\r\n").startswith(("=", "+", "-", "@")) else name
                yield writer.writerow((student_id, safe_name, exam_date, marks, total, round(marks * 100 / total, 2)))

        response = StreamingHttpResponse(rows(), content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="campusflow-students.csv"'
        response["Cache-Control"] = "private, no-store"
        return response


class StudentDetailView(PrivateStudentDataMixin, generics.RetrieveUpdateAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAdminUser, HasSchoolMembership]

    def get_queryset(self):
        return Student.objects.filter(school=self.request.school)

    def perform_update(self, serializer):
        if not serializer.validated_data:
            return
        with transaction.atomic():
            student = serializer.save()
            StudentChangeEvent.objects.create(
                school=self.request.school,
                student_id=student.pk,
                actor=self.request.user,
                action=StudentChangeEvent.Action.UPDATED,
            )


class StudentChangeHistoryView(PrivateStudentDataMixin, generics.ListAPIView):
    serializer_class = StudentChangeEventSerializer
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAdminUser, HasSchoolMembership]
    pagination_class = StudentPagination

    def get_queryset(self):
        student_id = self.kwargs["pk"]
        if not Student.objects.filter(pk=student_id, school=self.request.school).exists():
            raise NotFound("Student record not found.")
        return StudentChangeEvent.objects.filter(
            school=self.request.school,
            student_id=student_id,
        )


class StudentExportHistoryView(PrivateStudentDataMixin, generics.ListAPIView):
    serializer_class = StudentExportRequestSerializer
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAdminUser, HasSchoolMembership]
    pagination_class = StudentPagination

    def get_queryset(self):
        return StudentExportRequest.objects.filter(school=self.request.school).select_related("actor")


class AverageMarksView(PrivateStudentDataMixin, APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAdminUser, HasSchoolMembership]

    def get(self, request):
        result = Student.objects.filter(school=request.school).aggregate(
            student_count=Count("id"),
            average_marks=Avg("marks_obtained"),
            total_obtained=Sum("marks_obtained", default=0),
            total_marks=Sum("total_marks", default=0),
        )
        total_marks = result["total_marks"]
        average_percentage = result["total_obtained"] * 100 / total_marks if total_marks else 0

        return Response({
            "student_count": result["student_count"],
            "average_marks": round(float(result["average_marks"] or 0), 2),
            "average_percentage": round(float(average_percentage), 2),
        })


class PassedStudentsCountView(PrivateStudentDataMixin, APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAdminUser, HasSchoolMembership]

    def get(self, request):
        percentage = ExpressionWrapper(
            F("marks_obtained") * 100.0 / F("total_marks"),
            output_field=FloatField(),
        )
        count = (
            Student.objects.filter(school=request.school)
            .annotate(percentage=percentage)
            .filter(percentage__gte=33)
            .count()
        )

        return Response({
            "students_above_33_percent": count
        })


class HealthCheckView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        return JsonResponse({"status": "ok"})


class APIRootView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        endpoints = {
            "health": "healthz",
            "students": "student-list",
            "export_csv": "student-export",
            "export_history": "student-export-history",
            "create_student": "student-create",
            "average": "student-average",
            "passed_count": "student-count",
            "sign_in": "rest_framework:login",
        }
        return Response({
            "name": "CampusFlow API",
            "version": "1",
            "authentication": "Django session",
            "endpoints": {
                name: request.build_absolute_uri(reverse(route_name))
                for name, route_name in endpoints.items()
            },
        })
