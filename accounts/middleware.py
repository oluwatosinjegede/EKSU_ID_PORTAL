from django.shortcuts import redirect

class PasswordChangeRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            if getattr(request.user, 'must_change_password', False):
                allowed_paths = [
                    '/change-password/',
                    '/logout/',
                    '/admin/logout/',
                ]
                if not any(request.path.startswith(p) for p in allowed_paths):
                    return redirect('/change-password/')

        return self.get_response(request)
