from django.shortcuts import redirect
from django.urls import reverse, NoReverseMatch


class PasswordChangeRequiredMiddleware:
    """
    Forces users to change password before accessing the system.

    SAFE FOR:
    - Login & Admin login
    - Static / Media
    - API / Health checks
    - Railway probes
    - Prevents redirect loops
    - Does NOT break POST requests
    """

    def __init__(self, get_response):
        self.get_response = get_response

        # Resolve URL safely (startup-safe)
        try:
            self.change_password_url = reverse("force-change-password")
        except NoReverseMatch:
            self.change_password_url = "/change-password/"

        # Allowed URL prefixes (NO BLOCK)
        self.allowed_prefixes = (
            self.change_password_url,
            "/login/",
            "/logout/",
            "/admin/login/",
            "/admin/logout/",
            "/static/",
            "/media/",
            "/favicon.ico",
            "/health",
            "/api/",
        )

    def __call__(self, request):
        user = getattr(request, "user", None)

        # Skip if no authenticated user
        if not user or not user.is_authenticated:
            return self.get_response(request)

        # Skip for superusers (optional — remove to enforce)
        if user.is_superuser:
            return self.get_response(request)

        # Enforce password change
        if getattr(user, "must_change_password", False):

            path = request.path

            # Allow safe paths
            if any(path.startswith(p) for p in self.allowed_prefixes):
                return self.get_response(request)

            # DO NOT redirect during POST (prevents login/upload failure)
            if request.method == "POST":
                return self.get_response(request)

            # Prevent redirect loop
            if path != self.change_password_url:
                return redirect(self.change_password_url)

        return self.get_response(request)
