"""
Medical-Review Service - Complete Implementation
Product reviews, ratings, and user feedback
"""

from shared_ddd.base import ValueObject, Aggregate, DomainEvent, DomainService
from dataclasses import dataclass
from typing import Optional, List
import time
from django.db import models
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


# ============ DOMAIN LAYER ============

class ReviewId(ValueObject):
    def __init__(self, value: str):
        self.value = str(value)
    def __eq__(self, other):
        return isinstance(other, ReviewId) and self.value == other.value
    def __hash__(self):
        return hash(self.value)


class Rating(ValueObject):
    def __init__(self, value: int):
        if not (1 <= value <= 5):
            raise ValueError("Rating must be 1-5")
        self.value = value
    def __eq__(self, other):
        return isinstance(other, Rating) and self.value == other.value


@dataclass
class ReviewCreated(DomainEvent):
    review_id: str
    product_id: str
    user_id: str
    rating: int
    timestamp: int
    event_type: str = "ReviewCreated"

@dataclass
class ReviewUpvoted(DomainEvent):
    review_id: str
    upvotes: int
    timestamp: int
    event_type: str = "ReviewUpvoted"


class Review(Aggregate):
    """Review aggregate"""
    def __init__(self, review_id: ReviewId, product_id: str, user_id: str,
                 rating: Rating, title: str, content: str):
        super().__init__()
        self.review_id = review_id
        self.product_id = product_id
        self.user_id = user_id
        self.rating = rating
        self.title = title
        self.content = content
        self.upvotes = 0
        self.downvotes = 0
        self.is_verified_purchase = False
        self.created_at = int(time.time())
        
        self.domain_events.append(ReviewCreated(
            review_id=review_id.value,
            product_id=product_id,
            user_id=user_id,
            rating=rating.value,
            timestamp=self.created_at
        ))
    
    def upvote(self):
        """Add upvote"""
        self.upvotes += 1
        self.domain_events.append(ReviewUpvoted(
            review_id=self.review_id.value,
            upvotes=self.upvotes,
            timestamp=int(time.time())
        ))
    
    def mark_verified(self):
        """Mark as verified purchase"""
        self.is_verified_purchase = True


# ============ MODELS ============

class ReviewModel(models.Model):
    review_id = models.CharField(max_length=50, unique=True, db_index=True)
    product_id = models.CharField(max_length=50, db_index=True)
    user_id = models.CharField(max_length=50, db_index=True)
    rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    title = models.CharField(max_length=255)
    content = models.TextField()
    upvotes = models.IntegerField(default=0)
    downvotes = models.IntegerField(default=0)
    is_verified_purchase = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'medical_reviews'
        indexes = [
            models.Index(fields=['product_id', '-created_at']),
            models.Index(fields=['rating']),
        ]


class AverageRatingModel(models.Model):
    product_id = models.CharField(max_length=50, unique=True, db_index=True)
    average_rating = models.FloatField()
    total_reviews = models.IntegerField()
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'medical_average_ratings'


# ============ HTTP ENDPOINTS ============

class AddReviewView(APIView):
    """POST /api/reviews"""
    
    def post(self, request):
        """Add product review"""
        try:
            product_id = request.data.get('product_id')
            rating = request.data.get('rating')
            title = request.data.get('title')
            content = request.data.get('content')
            user_id = request.user.id if hasattr(request.user, 'id') else 'anonymous'
            
            review = ReviewModel.objects.create(
                review_id=f"review_{int(time.time() * 1000)}",
                product_id=product_id,
                user_id=user_id,
                rating=rating,
                title=title,
                content=content
            )
            
            # Update average rating
            avg = ReviewModel.objects.filter(product_id=product_id).aggregate(
                avg=models.Avg('rating'),
                count=models.Count('id')
            )
            
            AverageRatingModel.objects.update_or_create(
                product_id=product_id,
                defaults={
                    'average_rating': avg['avg'] or 0,
                    'total_reviews': avg['count'] or 0
                }
            )
            
            return Response({
                'success': True,
                'review_id': review.review_id
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            logger.error(f"Add review error: {e}")
            return Response({'success': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class GetProductReviewsView(APIView):
    """GET /api/reviews/{product_id}"""
    
    def get(self, request, product_id):
        """Get product reviews"""
        try:
            reviews = ReviewModel.objects.filter(product_id=product_id).order_by('-upvotes')
            avg = AverageRatingModel.objects.filter(product_id=product_id).first()
            
            review_list = [
                {
                    'review_id': r.review_id,
                    'rating': r.rating,
                    'title': r.title,
                    'content': r.content,
                    'upvotes': r.upvotes,
                    'verified': r.is_verified_purchase,
                    'created_at': r.created_at.isoformat()
                }
                for r in reviews[:20]
            ]
            
            return Response({
                'success': True,
                'product_id': product_id,
                'average_rating': avg.average_rating if avg else 0,
                'total_reviews': len(review_list),
                'reviews': review_list
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Get reviews error: {e}")
            return Response({'success': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UpvoteReviewView(APIView):
    """POST /api/reviews/{review_id}/upvote"""
    
    def post(self, request, review_id):
        """Upvote review"""
        try:
            review = ReviewModel.objects.get(review_id=review_id)
            review.upvotes += 1
            review.save()
            
            return Response({
                'success': True,
                'upvotes': review.upvotes
            }, status=status.HTTP_200_OK)
        
        except ReviewModel.DoesNotExist:
            return Response({'success': False, 'message': 'Review not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Upvote error: {e}")
            return Response({'success': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ============ URL ROUTING ============

from django.urls import path

medical_review_urls = [
    path('reviews/', AddReviewView.as_view(), name='add-review'),
    path('reviews/<str:product_id>/', GetProductReviewsView.as_view(), name='get-reviews'),
    path('reviews/<str:review_id>/upvote/', UpvoteReviewView.as_view(), name='upvote-review'),
]
