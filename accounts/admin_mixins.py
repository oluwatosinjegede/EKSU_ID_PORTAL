class RoleRestrictedAdminMixin:
    """
    Restricts Django Admin access by user role.
    Superusers always have access.
    """

    allowed_roles = []

    def _has_role_access(self, request):
        user = request.user

        if not user.is_authenticated:
            return False

        # Superuser always allowed
        if user.is_superuser:
            return True

        # Fallback: allow staff if no roles enforced
        if not self.allowed_roles:
            return user.is_staff

        # Defensive role lookup
        role = getattr(user, "role", None)

        return role in self.allowed_roles

    def has_module_permission(self, request):
        return self._has_role_access(request)

    def has_view_permission(self, request, obj=None):
        return self._has_role_access(request)

    def has_add_permission(self, request):
        return self._has_role_access(request)

    def has_change_permission(self, request, obj=None):
        return self._has_role_access(request)

    def has_delete_permission(self, request, obj=None):
        return self._has_role_access(request)
