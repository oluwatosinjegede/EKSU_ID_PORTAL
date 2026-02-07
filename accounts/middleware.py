from django.shortcuts import redirect
from django.urls import reverse


class PasswordChangeRequiredMiddleware:
    """
    Forces users to change password before accessing the system.

    Safe for:
    - Django Admin
    - Static & Media
    - API endpoints
    - Health checks / Railway probes
    - Prevents redirect loops
    """

    def __init__(self, get_response):
        self.get_response = get_response

        # Resolve URL once (faster + safer than hardcoding path)
        try:
            self.change_password_url = reverse("force-change-password")
        except Exception:
            self.change_password_url = "/change-password/"

        self.allowed_prefixes = (
            self.change_password_url,
            "/logout/",
            "/admin/logout/",
            "/static/",
            "/media/",
            "/favicon.ico",
            "/health",
            "/api/auth/",  # allow login/token endpoints
        )

    def __call__(self, request):
        user = getattr(request, "user", None)

        if user and user.is_authenticated:

            # Skip for superusers (optional — remove if you want enforcement)
            if user.is_superuser:
                return self.get_response(request)

            if getattr(user, "must_change_password", False):

                path = request.path

                # Allow safe paths
                if not any(path.startswith(p) for p in self.allowed_prefixes):
                    if path != self.change_password_url:
                        return redirect(self.change_password_url)

        return self.get_response(request)
