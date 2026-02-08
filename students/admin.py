from django.contrib import admin
from django.db.models import Q
from .models import Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):

    list_display = (
        "matric_number",
        "first_name",
        "last_name",
        "department",
        "level",
    )

    list_filter = ("department", "level")

    ordering = ("matric_number",)

    # ONLY use fields that truly exist
    search_fields = (
        "matric_number",
        "first_name",
        "last_name",
        "department",
        "user__username",
    )

    # Prevent admin crash even if bad field somehow appears
    def get_search_results(self, request, queryset, search_term):
        try:
            return super().get_search_results(request, queryset, search_term)
        except Exception:
            # Fallback safe search (never crash)
            queryset = queryset.filter(
                Q(matric_number__icontains=search_term)
                | Q(first_name__icontains=search_term)
                | Q(last_name__icontains=search_term)
                | Q(department__icontains=search_term)
                | Q(user__username__icontains=search_term)
            )
            return queryset, False
