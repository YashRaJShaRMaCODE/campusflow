from rest_framework.permissions import SAFE_METHODS, BasePermission

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
        request.school_membership = membership
        return True


class CanManageSchoolRecords(HasSchoolMembership):
    message = "A manager role is required to change student records."

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.method in SAFE_METHODS or request.school_membership.role == SchoolMembership.Role.MANAGER
