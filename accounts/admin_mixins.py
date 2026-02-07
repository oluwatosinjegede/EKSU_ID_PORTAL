class RoleRestrictedAdminMixin:
    """
    Role-based restriction for Django Admin.

    Features:
    - Superusers always allowed
    - Optional allowed_roles list
    - Safe fallback to staff if no roles defined
    - Optional read-only access for non-authorized users
    - Prevents accidental admin lockout
    """

    allowed_roles = []          # Roles allowed full access
    readonly_for_others = False # If True, non-allowed users get read-only access

    # =====================================================
    # INTERNAL CHECK
    # =====================================================
    def _has_role_access(self, request):
        user = request.user

        if not user.is_authenticated:
            return False

        # Superuser always allowed
        if user.is_superuser:
            return True

        # If no roles configured -> allow staff (safe fallback)
        if not self.allowed_roles:
            return user.is_staff

        role = getattr(user, "role", None)
        return role in self.allowed_roles

    # =====================================================
    # MODULE ACCESS
    # =====================================================
    def has_module_permission(self, request):
        return self._has_role_access(request)

    # =====================================================
    # VIEW PERMISSION
    # =====================================================
    def has_view_permission(self, request, obj=None):
        if self._has_role_access(request):
            return True

        # Optional read-only fallback
        return self.readonly_for_others and request.user.is_staff

    # =====================================================
    # ADD PERMISSION
    # =====================================================
    def has_add_permission(self, request):
        return self._has_role_access(request)

    # =====================================================
    # CHANGE PERMISSION
    # =====================================================
    def has_change_permission(self, request, obj=None):
        return self._has_role_access(request)

    # =====================================================
    # DELETE PERMISSION
    # =====================================================
    def has_delete_permission(self, request, obj=None):
        return self._has_role_access(request)

    # =====================================================
    # OPTIONAL: FORCE READ-ONLY MODE
    # =====================================================
    def get_readonly_fields(self, request, obj=None):
        if self._has_role_access(request):
            return super().get_readonly_fields(request, obj)

        if self.readonly_for_others:
            # Make ALL fields readonly
            return [f.name for f in self.model._meta.fields]

        return super().get_readonly_fields(request, obj)
