from django.urls import path
from app.views import ProductListCreate, ProductDetail, HealthView

urlpatterns = [
    path('products/',        ProductListCreate.as_view(), name='product-list'),
    path('products/<int:pk>/', ProductDetail.as_view(),   name='product-detail'),
    path('health/',          HealthView.as_view(),        name='health'),
]
