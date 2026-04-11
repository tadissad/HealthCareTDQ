from django.urls import path
from app.views import LoginView, ValidateTokenView, HealthView

urlpatterns = [
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/validate/', ValidateTokenView.as_view(), name='auth-validate'),
    path('health/', HealthView.as_view(), name='health'),
]
