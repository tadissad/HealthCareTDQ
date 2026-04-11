from django.urls import path
from app.views import ReviewListCreate, ReviewDetail, ReviewSummary, HealthView

urlpatterns = [
    path('reviews/',                      ReviewListCreate.as_view(), name='review-list'),
    path('reviews/<int:pk>/',             ReviewDetail.as_view(),     name='review-detail'),
    path('reviews/summary/',              ReviewSummary.as_view(),    name='review-summary'),
    path('health/',                       HealthView.as_view(),       name='health'),
]
