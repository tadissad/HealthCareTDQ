from django.urls import path
from app.views import CustomerListCreate, CustomerDetail, CustomerByAccount, CustomerMembership, HealthView

urlpatterns = [
    path('customers/',                           CustomerListCreate.as_view(),  name='customer-list'),
    path('customers/<int:pk>/',                  CustomerDetail.as_view(),      name='customer-detail'),
    path('customers/by-account/<int:account_id>/', CustomerByAccount.as_view(), name='customer-by-account'),
    path('customers/by-account/<int:account_id>/membership/', CustomerMembership.as_view(), name='customer-membership'),
    path('health/', HealthView.as_view(), name='health'),
]
