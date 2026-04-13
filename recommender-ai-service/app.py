"""
Recommender AI Service - ML-based recommendations
Personalized product and treatment recommendations
"""

from shared_ddd.base import ValueObject, Aggregate, DomainEvent, DomainService
from dataclasses import dataclass
from typing import Optional, List, Dict
import time
from django.db import models
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


# ============ DOMAIN LAYER ============

class RecommendationId(ValueObject):
    def __init__(self, value: str):
        self.value = str(value)
    def __eq__(self, other):
        return isinstance(other, RecommendationId) and self.value == other.value
    def __hash__(self):
        return hash(self.value)


class RecommendationType(ValueObject):
    TYPES = ['PRODUCT', 'TREATMENT', 'PREVENTION', 'LIFESTYLE']
    
    def __init__(self, value: str):
        if value not in self.TYPES:
            raise ValueError(f"Invalid type: {value}")
        self.value = value


class ConfidenceScore(ValueObject):
    def __init__(self, value: float):
        if not (0.0 <= value <= 1.0):
            raise ValueError("Score must be 0-1")
        self.value = value


@dataclass
class RecommendationGenerated(DomainEvent):
    recommendation_id: str
    user_id: str
    item_id: str
    confidence: float
    timestamp: int
    event_type: str = "RecommendationGenerated"

@dataclass
class RecommendationAccepted(DomainEvent):
    recommendation_id: str
    user_id: str
    timestamp: int
    event_type: str = "RecommendationAccepted"


class Recommendation(Aggregate):
    """Recommendation aggregate"""
    def __init__(self, rec_id: RecommendationId, user_id: str, item_id: str,
                 rec_type: RecommendationType, confidence: ConfidenceScore):
        super().__init__()
        self.rec_id = rec_id
        self.user_id = user_id
        self.item_id = item_id
        self.rec_type = rec_type
        self.confidence = confidence
        self.explanation = ""
        self.is_accepted = False
        self.created_at = int(time.time())
        
        self.domain_events.append(RecommendationGenerated(
            recommendation_id=rec_id.value,
            user_id=user_id,
            item_id=item_id,
            confidence=confidence.value,
            timestamp=self.created_at
        ))
    
    def accept(self):
        """User accepts recommendation"""
        self.is_accepted = True
        self.domain_events.append(RecommendationAccepted(
            recommendation_id=self.rec_id.value,
            user_id=self.user_id,
            timestamp=int(time.time())
        ))


class RecommenderModel(Aggregate):
    """Collaborative filtering model"""
    def __init__(self, model_id: str, version: int):
        super().__init__()
        self.model_id = model_id
        self.version = version
        self.created_at = int(time.time())
        self.accuracy = 0.0
        self.is_active = False
    
    def activate(self):
        """Activate model for recommendations"""
        self.is_active = True
    
    def deactivate(self):
        """Deactivate model"""
        self.is_active = False


# ============ DOMAIN SERVICES ============

class RecommendationEngine(DomainService):
    """Generate recommendations"""
    
    def __init__(self):
        self.user_item_interactions = {}  # {user_id: {item_id: score}}
    
    def generate_recommendations(self, user_id: str, count: int = 5) -> List[Dict]:
        """Generate top N recommendations for user"""
        try:
            # Simplified collaborative filtering
            user_interactions = self.user_item_interactions.get(user_id, {})
            
            # Get similar users
            similar_users = self._find_similar_users(user_id)
            
            # Collect recommendations from similar users
            recommendations = {}
            for sim_user in similar_users:
                sim_interactions = self.user_item_interactions.get(sim_user, {})
                for item_id, score in sim_interactions.items():
                    if item_id not in user_interactions:
                        if item_id not in recommendations:
                            recommendations[item_id] = []
                        recommendations[item_id].append(score)
            
            # Score recommendations
            scored_recs = [
                {
                    'item_id': item_id,
                    'confidence': sum(scores) / len(scores),
                    'votes': len(scores)
                }
                for item_id, scores in recommendations.items()
            ]
            
            # Sort by confidence and return top N
            scored_recs.sort(key=lambda x: x['confidence'], reverse=True)
            return scored_recs[:count]
        
        except Exception as e:
            logger.error(f"Recommendation generation error: {e}")
            return []
    
    def _find_similar_users(self, user_id: str, k: int = 5) -> List[str]:
        """Find similar users using cosine similarity"""
        # Simplified similarity based on shared items
        user_items = set(self.user_item_interactions.get(user_id, {}).keys())
        
        similarities = []
        for other_user, other_items in self.user_item_interactions.items():
            if other_user == user_id:
                continue
            
            other_set = set(other_items.keys())
            intersection = len(user_items & other_set)
            union = len(user_items | other_set)
            
            if union > 0:
                similarity = intersection / union
                similarities.append((other_user, similarity))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        return [u for u, sim in similarities[:k]]
    
    def record_interaction(self, user_id: str, item_id: str, score: float):
        """Record user-item interaction"""
        if user_id not in self.user_item_interactions:
            self.user_item_interactions[user_id] = {}
        
        self.user_item_interactions[user_id][item_id] = score


# ============ MODELS ============

class RecommendationModel(models.Model):
    recommendation_id = models.CharField(max_length=50, unique=True, db_index=True)
    user_id = models.CharField(max_length=50, db_index=True)
    item_id = models.CharField(max_length=50)
    rec_type = models.CharField(max_length=50)
    confidence = models.FloatField()
    explanation = models.TextField()
    is_accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'recommender_recommendations'
        indexes = [
            models.Index(fields=['user_id', '-created_at']),
            models.Index(fields=['item_id']),
        ]


# ============ HTTP ENDPOINTS ============

class GetRecommendationsView(APIView):
    """GET /api/recommendations/{user_id}"""
    
    def get(self, request, user_id):
        """Get personalized recommendations"""
        try:
            count = request.query_params.get('count', 5, type=int)
            
            recs = RecommendationModel.objects.filter(user_id=user_id).order_by('-confidence')[:count]
            
            rec_list = [
                {
                    'recommendation_id': r.recommendation_id,
                    'item_id': r.item_id,
                    'type': r.rec_type,
                    'confidence': r.confidence,
                    'explanation': r.explanation,
                    'accepted': r.is_accepted
                }
                for r in recs
            ]
            
            return Response({
                'success': True,
                'user_id': user_id,
                'recommendations': rec_list
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Get recommendations error: {e}")
            return Response({'success': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class GenerateRecommendationsView(APIView):
    """POST /api/recommendations/generate"""
    
    def post(self, request):
        """Generate recommendations for user"""
        try:
            user_id = request.data.get('user_id')
            count = request.data.get('count', 5)
            rec_type = request.data.get('type', 'PRODUCT')
            
            # Simplified generation - in production would use ML model
            recommendations = [
                {
                    'recommendation_id': f"rec_{i}_{int(time.time())}",
                    'user_id': user_id,
                    'item_id': f"item_{i}",
                    'type': rec_type,
                    'confidence': 0.8 - (i * 0.05),
                }
                for i in range(count)
            ]
            
            # Save to database
            for rec in recommendations:
                RecommendationModel.objects.create(
                    recommendation_id=rec['recommendation_id'],
                    user_id=user_id,
                    item_id=rec['item_id'],
                    rec_type=rec_type,
                    confidence=rec['confidence'],
                    explanation="Generated based on user preferences"
                )
            
            return Response({
                'success': True,
                'recommendations': recommendations
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            logger.error(f"Generate recommendations error: {e}")
            return Response({'success': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AcceptRecommendationView(APIView):
    """POST /api/recommendations/{recommendation_id}/accept"""
    
    def post(self, request, recommendation_id):
        """User accepts recommendation"""
        try:
            rec = RecommendationModel.objects.get(recommendation_id=recommendation_id)
            rec.is_accepted = True
            rec.save()
            
            return Response({
                'success': True,
                'message': 'Recommendation accepted'
            }, status=status.HTTP_200_OK)
        
        except RecommendationModel.DoesNotExist:
            return Response({'success': False, 'message': 'Recommendation not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Accept recommendation error: {e}")
            return Response({'success': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ============ URL ROUTING ============

from django.urls import path

recommender_urls = [
    path('recommendations/<str:user_id>/', GetRecommendationsView.as_view(), name='get-recommendations'),
    path('recommendations/generate/', GenerateRecommendationsView.as_view(), name='generate-recommendations'),
    path('recommendations/<str:recommendation_id>/accept/', AcceptRecommendationView.as_view(), name='accept-recommendation'),
]
