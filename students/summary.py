from django.db.models import Avg, Count, ExpressionWrapper, F, FloatField, Q, Sum
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Student
from .permissions import HasSchoolMembership


class SchoolSummaryView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAdminUser, HasSchoolMembership]

    def get(self, request):
        percentage = ExpressionWrapper(
            F("marks_obtained") * 100.0 / F("total_marks"),
            output_field=FloatField(),
        )
        result = Student.objects.filter(school=request.school).annotate(
            percentage=percentage,
        ).aggregate(
            student_count=Count("id"),
            average_marks=Avg("marks_obtained"),
            total_obtained=Sum("marks_obtained", default=0),
            total_marks=Sum("total_marks", default=0),
            students_above_33_percent=Count("id", filter=Q(percentage__gte=33)),
        )
        total_marks = result["total_marks"]
        response = Response({
            "student_count": result["student_count"],
            "average_marks": round(float(result["average_marks"] or 0), 2),
            "average_percentage": round(float(result["total_obtained"] * 100 / total_marks), 2)
            if total_marks else 0,
            "students_above_33_percent": result["students_above_33_percent"],
        })
        response["Cache-Control"] = "private, no-store"
        return response
