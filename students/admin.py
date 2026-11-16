
from django.contrib import admin

from .models import School, SchoolMembership

admin.site.register(School)


@admin.register(SchoolMembership)
class SchoolMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "school", "role", "created_at")
    list_filter = ("school", "role")
    search_fields = ("user__username", "user__email", "school__name")
