"""
Auth Service - URL Configuration
Django URL routing for all authentication endpoints
"""

from django.urls import path
from auth_service.interfaces.http.views import (
    RegisterView,
    LoginView,
    LogoutView,
    ValidateTokenView,
    CheckAccessView,
    GetUserView,
    AssignRoleView,
    HealthCheckView,
)

urlpatterns = [
    # Authentication
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/logout/', LogoutView.as_view(), name='auth-logout'),
    path('auth/validate/', ValidateTokenView.as_view(), name='auth-validate'),
    path('auth/check-access/', CheckAccessView.as_view(), name='auth-check-access'),
    path('auth/refresh/', ValidateTokenView.as_view(), name='auth-refresh'),
    
    # User Management
    path('auth/users/<str:user_id>/', GetUserView.as_view(), name='get-user'),
    path('auth/assign-role/', AssignRoleView.as_view(), name='assign-role'),
    
    # Health
    path('auth/health/', HealthCheckView.as_view(), name='health-check'),
]
