import math

from django.db.models import Avg, Count, ExpressionWrapper, F, FloatField, Sum
from django.http import JsonResponse
from django.urls import reverse
from django.utils.dateparse import parse_date
from rest_framework import filters, generics
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Student
from .serializers import StudentSerializer


class StudentCreateView(generics.CreateAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAdminUser]


class StudentPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 100


class StudentListView(generics.ListAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAdminUser]
    pagination_class = StudentPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["name", "date", "marks_obtained", "total_marks"]
    ordering = ["-date", "name", "id"]

    def get_queryset(self):
        queryset = super().get_queryset()
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


class StudentDetailView(generics.RetrieveUpdateAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAdminUser]


class AverageMarksView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAdminUser]

    def get(self, request):
        result = Student.objects.aggregate(
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


class PassedStudentsCountView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAdminUser]

    def get(self, request):
        percentage = ExpressionWrapper(
            F("marks_obtained") * 100.0 / F("total_marks"),
            output_field=FloatField(),
        )
        count = Student.objects.annotate(percentage=percentage).filter(percentage__gte=33).count()

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
            "create_student": "student-create",
            "average": "student-average",
            "passed_count": "student-count",
            "sign_in": "rest_framework:login",
        }
        return Response({
            "name": "Student Records API",
            "version": "1",
            "authentication": "Django session",
            "endpoints": {
                name: request.build_absolute_uri(reverse(route_name))
                for name, route_name in endpoints.items()
            },
        })
