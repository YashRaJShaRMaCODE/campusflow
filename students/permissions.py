from rest_framework.permissions import BasePermission

from .models import SchoolMembership


class HasSchoolMembership(BasePermission):
    message = "A school membership is required to access student records."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        membership = SchoolMembership.objects.select_related("school").filter(
            user=request.user
        ).first()
        if not membership:
            return False
        request.school = membership.school
        return True
