from django.db.models import Avg, Count, ExpressionWrapper, F, FloatField, Sum
from django.http import JsonResponse
from django.urls import reverse
from rest_framework import filters, generics
from rest_framework.authentication import SessionAuthentication
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
