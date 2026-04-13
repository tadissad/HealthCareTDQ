"""
Clinical-Advisory Service - Interface Layer - HTTP Views
Django REST Framework views for consultation management
"""

import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.serializers import Serializer, CharField, IntegerField, ListSerializer
from clinical_advisory_service.application.commands_queries import (
    InitiateConsultation, AddPatientMessage, PerformAIScreening,
    AddAIRecommendation, RequestClinicianReview, EndorseRecommendation,
    RejectRecommendation, CompleteConsultation, CancelConsultation,
    EscalateUrgentCase,
    GetConsultationById, GetPatientConsultations, ListActiveConsultations,
    ListUrgentCases, GetConsultationMessages, GetConsultationRecommendations
)
from clinical_advisory_service.application.handlers import (
    InitiateConsultationHandler, AddPatientMessageHandler,
    PerformAIScreeningHandler, AddAIRecommendationHandler,
    EndorseRecommendationHandler, RejectRecommendationHandler,
    CompleteConsultationHandler, EscalateUrgentCaseHandler,
    GetConsultationByIdHandler, GetPatientConsultationsHandler,
    ListActiveConsultationsHandler, ListUrgentCasesHandler,
    GetConsultationMessagesHandler, GetConsultationRecommendationsHandler
)

logger = logging.getLogger(__name__)


# ============ Request/Response Serializers ============

class InitiateConsultationSerializer(Serializer):
    """Request to initiate new consultation"""
    patient_id = CharField(max_length=36)
    chief_complaint = CharField(max_length=1000)
    medical_background = CharField(required=False, allow_blank=True)


class AddMessageSerializer(Serializer):
    """Request to add message"""
    content = CharField(max_length=5000)
    message_type = CharField(max_length=50)  # PATIENT, AI, CLINICIAN


class AddRecommendationSerializer(Serializer):
    """Request to add recommendation"""
    recommendation_type = CharField(max_length=50)
    title = CharField(max_length=255)
    description = CharField(max_length=2000)
    medication_name = CharField(required=False, allow_blank=True)
    dosage = CharField(required=False, allow_blank=True)
    frequency = CharField(required=False, allow_blank=True)
    confidence = IntegerField(min_value=0, max_value=100, default=50)


class ReviewRecommendationSerializer(Serializer):
    """Request to endorse/reject recommendation"""
    recommendation_id = CharField(max_length=36)
    action = CharField(max_length=10)  # ENDORSE, REJECT
    notes = CharField(required=False, allow_blank=True)


class ConsultationDetailSerializer(Serializer):
    """Full consultation details"""
    consultation_id = CharField()
    patient_id = CharField()
    status = CharField()
    chief_complaint = CharField()
    urgency_level = CharField()
    is_urgent_case = CharField()
    initiated_at = CharField()
    message_count = IntegerField()
    recommendation_count = IntegerField()


# ============ API Endpoints ============

class ConsultationInitiateView(APIView):
    """POST /api/consultations/initiate"""
    
    def post(self, request):
        """Initiate new consultation"""
        try:
            serializer = InitiateConsultationSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            command = InitiateConsultation(
                patient_id=serializer.validated_data['patient_id'],
                chief_complaint=serializer.validated_data['chief_complaint'],
                medical_background=serializer.validated_data.get('medical_background', {})
            )
            
            handler = InitiateConsultationHandler()
            result = handler.handle(command)
            
            return Response({
                'success': True,
                'consultation_id': result.consultation_id,
                'status': result.status,
                'message': 'Consultation initiated successfully'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error initiating consultation: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class ConsultationDetailView(APIView):
    """GET /api/consultations/{consultation_id}"""
    
    def get(self, request, consultation_id):
        """Get consultation details"""
        try:
            query = GetConsultationById(consultation_id=consultation_id)
            handler = GetConsultationByIdHandler()
            result = handler.handle(query)
            
            if not result:
                return Response({
                    'success': False,
                    'error': 'Consultation not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            return Response({
                'success': True,
                'consultation': result
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error retrieving consultation: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class PatientConsultationsView(APIView):
    """GET /api/patient-consultations/{patient_id}"""
    
    def get(self, request, patient_id):
        """Get all consultations for patient"""
        try:
            query = GetPatientConsultations(patient_id=patient_id)
            handler = GetPatientConsultationsHandler()
            results = handler.handle(query)
            
            return Response({
                'success': True,
                'consultations': results,
                'count': len(results)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error retrieving patient consultations: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class ActiveConsultationsView(APIView):
    """GET /api/consultations/active"""
    
    def get(self, request):
        """Get all active consultations"""
        try:
            query = ListActiveConsultations()
            handler = ListActiveConsultationsHandler()
            results = handler.handle(query)
            
            return Response({
                'success': True,
                'consultations': results,
                'count': len(results)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error retrieving active consultations: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class UrgentConsultationsView(APIView):
    """GET /api/consultations/urgent"""
    
    def get(self, request):
        """Get all urgent consultations"""
        try:
            query = ListUrgentCases()
            handler = ListUrgentCasesHandler()
            results = handler.handle(query)
            
            return Response({
                'success': True,
                'consultations': results,
                'count': len(results)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error retrieving urgent consultations: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class AddMessageView(APIView):
    """POST /api/consultations/{consultation_id}/messages"""
    
    def post(self, request, consultation_id):
        """Add message to consultation"""
        try:
            serializer = AddMessageSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            command = AddPatientMessage(
                consultation_id=consultation_id,
                content=serializer.validated_data['content'],
                message_type=serializer.validated_data.get('message_type', 'PATIENT')
            )
            
            handler = AddPatientMessageHandler()
            result = handler.handle(command)
            
            return Response({
                'success': True,
                'message_id': result.message_id,
                'message': 'Message added successfully'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error adding message: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class GetMessagesView(APIView):
    """GET /api/consultations/{consultation_id}/messages"""
    
    def get(self, request, consultation_id):
        """Get all messages for consultation"""
        try:
            query = GetConsultationMessages(consultation_id=consultation_id)
            handler = GetConsultationMessagesHandler()
            results = handler.handle(query)
            
            return Response({
                'success': True,
                'messages': results,
                'count': len(results)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error retrieving messages: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class AddRecommendationView(APIView):
    """POST /api/consultations/{consultation_id}/recommendations"""
    
    def post(self, request, consultation_id):
        """Add recommendation to consultation"""
        try:
            serializer = AddRecommendationSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            command = AddAIRecommendation(
                consultation_id=consultation_id,
                recommendation_type=serializer.validated_data['recommendation_type'],
                title=serializer.validated_data['title'],
                description=serializer.validated_data['description'],
                medication_name=serializer.validated_data.get('medication_name'),
                dosage=serializer.validated_data.get('dosage'),
                frequency=serializer.validated_data.get('frequency'),
                confidence=serializer.validated_data.get('confidence', 50) / 100.0
            )
            
            handler = AddAIRecommendationHandler()
            result = handler.handle(command)
            
            return Response({
                'success': True,
                'recommendation_id': result.recommendation_id,
                'message': 'Recommendation added successfully'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error adding recommendation: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class GetRecommendationsView(APIView):
    """GET /api/consultations/{consultation_id}/recommendations"""
    
    def get(self, request, consultation_id):
        """Get all recommendations for consultation"""
        try:
            query = GetConsultationRecommendations(consultation_id=consultation_id)
            handler = GetConsultationRecommendationsHandler()
            results = handler.handle(query)
            
            return Response({
                'success': True,
                'recommendations': results,
                'count': len(results)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error retrieving recommendations: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class ReviewRecommendationView(APIView):
    """POST /api/consultations/{consultation_id}/recommendations/{recommendation_id}/review"""
    
    def post(self, request, consultation_id, recommendation_id):
        """Endorse or reject recommendation"""
        try:
            serializer = ReviewRecommendationSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            action = serializer.validated_data['action'].upper()
            notes = serializer.validated_data.get('notes', '')
            
            if action == 'ENDORSE':
                command = EndorseRecommendation(
                    consultation_id=consultation_id,
                    recommendation_id=recommendation_id,
                    clinician_notes=notes
                )
                handler = EndorseRecommendationHandler()
            elif action == 'REJECT':
                command = RejectRecommendation(
                    consultation_id=consultation_id,
                    recommendation_id=recommendation_id,
                    clinician_notes=notes
                )
                handler = RejectRecommendationHandler()
            else:
                return Response({
                    'success': False,
                    'error': 'Invalid action. Use ENDORSE or REJECT'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            result = handler.handle(command)
            
            return Response({
                'success': True,
                'message': f'Recommendation {action.lower()}d successfully'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error reviewing recommendation: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class CompleteConsultationView(APIView):
    """POST /api/consultations/{consultation_id}/complete"""
    
    def post(self, request, consultation_id):
        """Complete consultation"""
        try:
            command = CompleteConsultation(consultation_id=consultation_id)
            handler = CompleteConsultationHandler()
            result = handler.handle(command)
            
            return Response({
                'success': True,
                'message': 'Consultation completed successfully'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error completing consultation: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class CancelConsultationView(APIView):
    """POST /api/consultations/{consultation_id}/cancel"""
    
    def post(self, request, consultation_id):
        """Cancel consultation"""
        try:
            command = CancelConsultation(consultation_id=consultation_id)
            handler = CompleteConsultationHandler()  # Reuse handler for cancel logic
            result = handler.handle(command)
            
            return Response({
                'success': True,
                'message': 'Consultation cancelled successfully'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error cancelling consultation: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class EscalateUrgentView(APIView):
    """POST /api/consultations/{consultation_id}/escalate"""
    
    def post(self, request, consultation_id):
        """Escalate urgent case"""
        try:
            command = EscalateUrgentCase(consultation_id=consultation_id)
            handler = EscalateUrgentCaseHandler()
            result = handler.handle(command)
            
            return Response({
                'success': True,
                'escalation_id': result.escalation_id,
                'message': 'Case escalated to emergency protocols'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error escalating case: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
