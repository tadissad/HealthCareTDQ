"""Giới hạn tài khoản staff chỉ dùng được khu vực /staff/ (và đăng xuất)."""
from django.shortcuts import redirect


class RestrictStaffToPortalMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.session.get('role') == 'staff':
            path = request.path
            allowed = (
                path.startswith('/staff/'),
                path in ('/login/', '/logout/'),
                path.startswith('/static/'),
            )
            if not allowed:
                return redirect('/staff/products/')
        return self.get_response(request)
