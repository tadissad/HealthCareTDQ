from django.urls import path
from app.views import CartView, CartItemCreate, CartItemDetail, HealthView

urlpatterns = [
    path('carts/<int:customer_id>/', CartView.as_view(),       name='cart-by-customer'),
    path('carts/',                   CartItemCreate.as_view(),  name='cart-create'),
    path('cart-items/',              CartItemCreate.as_view(),  name='cart-item-create'),
    path('cart-items/<int:pk>/',     CartItemDetail.as_view(),  name='cart-item-detail'),
    path('health/',                  HealthView.as_view(),      name='health'),
]
