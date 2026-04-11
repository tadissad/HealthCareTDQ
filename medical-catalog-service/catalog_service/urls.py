from django.urls import path
from app.views import CategoryListCreate, CategoryDetail, SubCategoryListCreate, HealthView

urlpatterns = [
    path('categories/',            CategoryListCreate.as_view(),    name='category-list'),
    path('categories/<int:pk>/',   CategoryDetail.as_view(),        name='category-detail'),
    path('subcategories/',         SubCategoryListCreate.as_view(), name='subcategory-list'),
    path('health/',                HealthView.as_view(),            name='health'),
]
