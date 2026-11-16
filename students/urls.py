from django.urls import path

from .summary import SchoolSummaryView
from .views import (
    APIRootView,
    AverageMarksView,
    HealthCheckView,
    PassedStudentsCountView,
    StudentChangeHistoryView,
    StudentCreateView,
    StudentCsvExportView,
    StudentDetailView,
    StudentExportHistoryView,
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
        "students/export.csv",
        StudentCsvExportView.as_view(),
        name="student-export",
    ),
    path(
        "students/exports/",
        StudentExportHistoryView.as_view(),
        name="student-export-history",
    ),
    path(
        "students/",
        StudentListView.as_view(),
        name="student-list",
    ),
    path(
        "students/<int:pk>/",
        StudentDetailView.as_view(),
        name="student-detail",
    ),
    path(
        "students/<int:pk>/changes/",
        StudentChangeHistoryView.as_view(),
        name="student-change-history",
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
    path("students/summary/", SchoolSummaryView.as_view(), name="student-summary"),
]
