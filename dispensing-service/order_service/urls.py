from django.urls import path
from app.views import OrderListCreate, OrderDetail, OrderCreate, HealthView

urlpatterns = [
    path('orders/',              OrderListCreate.as_view(), name='order-list'),
    path('orders/<int:pk>/',     OrderDetail.as_view(),     name='order-detail'),
    path('orders/create/',       OrderCreate.as_view(),     name='order-create'),
    path('health/',              HealthView.as_view(),      name='health'),
]
