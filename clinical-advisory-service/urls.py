"""
Clinical-Advisory Service - URL Configuration
Django URL routing for all consultation endpoints
"""

from django.urls import path
from clinical_advisory_service.interfaces.http.views import (
    ConsultationInitiateView,
    ConsultationDetailView,
    PatientConsultationsView,
    ActiveConsultationsView,
    UrgentConsultationsView,
    AddMessageView,
    GetMessagesView,
    AddRecommendationView,
    GetRecommendationsView,
    ReviewRecommendationView,
    CompleteConsultationView,
    CancelConsultationView,
    EscalateUrgentView,
)

urlpatterns = [
    # Consultation Management
    path('consultations/initiate/', ConsultationInitiateView.as_view(), name='initiate-consultation'),
    path('consultations/<str:consultation_id>/', ConsultationDetailView.as_view(), name='consultation-detail'),
    path('consultations/active/', ActiveConsultationsView.as_view(), name='active-consultations'),
    path('consultations/urgent/', UrgentConsultationsView.as_view(), name='urgent-consultations'),
    path('consultations/<str:consultation_id>/complete/', CompleteConsultationView.as_view(), name='complete-consultation'),
    path('consultations/<str:consultation_id>/cancel/', CancelConsultationView.as_view(), name='cancel-consultation'),
    path('consultations/<str:consultation_id>/escalate/', EscalateUrgentView.as_view(), name='escalate-urgent'),
    
    # Patient Consultations
    path('patient-consultations/<str:patient_id>/', PatientConsultationsView.as_view(), name='patient-consultations'),
    
    # Messages
    path('consultations/<str:consultation_id>/messages/', AddMessageView.as_view(), name='add-message'),
    path('consultations/<str:consultation_id>/messages/list/', GetMessagesView.as_view(), name='get-messages'),
    
    # Recommendations
    path('consultations/<str:consultation_id>/recommendations/', AddRecommendationView.as_view(), name='add-recommendation'),
    path('consultations/<str:consultation_id>/recommendations/list/', GetRecommendationsView.as_view(), name='get-recommendations'),
    path('consultations/<str:consultation_id>/recommendations/<str:recommendation_id>/review/', ReviewRecommendationView.as_view(), name='review-recommendation'),
]
