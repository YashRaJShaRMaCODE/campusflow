from django.urls import path

from .views import (
    APIRootView,
    AverageMarksView,
    HealthCheckView,
    PassedStudentsCountView,
    StudentCreateView,
    StudentListView,
)

urlpatterns = [
    path("", APIRootView.as_view(), name="api-root"),
    path("healthz/", HealthCheckView.as_view(), name="healthz"),
    path(
        "students/add/",
        StudentCreateView.as_view(),
        name="student-create",
    ),

    path(
        "students/",
        StudentListView.as_view(),
        name="student-list",
    ),

    path(
        "students/average/",
        AverageMarksView.as_view(),
        name="student-average",
    ),

    path(
        "students/count/",
        PassedStudentsCountView.as_view(),
        name="student-count",
    ),
]
