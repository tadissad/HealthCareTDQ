"""
Medical-Catalog Service - Application & Interface
"""

from dataclasses import dataclass
from django.db import models
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


# ============ COMMANDS & QUERIES ============

@dataclass
class AddProductCommand:
    name: str
    code: str
    category: str
    price: float
    description: str = ""

@dataclass
class SearchProductsQuery:
    query: str
    category: str = None
    price_min: float = None
    price_max: float = None
    limit: int = 50

@dataclass
class GetProductByIdQuery:
    product_id: str


# ============ ORM MODELS ============

class ProductModel(models.Model):
    CATEGORY_CHOICES = [
        ('PRESCRIPTION_DRUG', 'Prescription Drug'),
        ('OTC_DRUG', 'Over-The-Counter'),
        ('SUPPLEMENT', 'Supplement'),
        ('MEDICAL_DEVICE', 'Medical Device'),
        ('WELLNESS', 'Wellness'),
        ('DIAGNOSTIC', 'Diagnostic'),
    ]
    
    product_id = models.CharField(max_length=50, unique=True, db_index=True)
    code = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=255, db_index=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    stock_quantity = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'medical_products'
        indexes = [
            models.Index(fields=['is_active', '-created_at']),
            models.Index(fields=['category', 'price']),
        ]


# ============ HTTP ENDPOINTS ============

class SearchProductsView(APIView):
    """POST /api/products/search"""
    
    def post(self, request):
        """Search products"""
        try:
            query = request.data.get('query', '')
            category = request.data.get('category')
            price_min = request.data.get('price_min')
            price_max = request.data.get('price_max')
            
            filters = {'is_active': True}
            if category:
                filters['category'] = category
            
            products = ProductModel.objects.filter(**filters)
            
            if query:
                products = products.filter(name__icontains=query)
            
            if price_min:
                products = products.filter(price__gte=price_min)
            if price_max:
                products = products.filter(price__lte=price_max)
            
            results = [
                {
                    'product_id': p.product_id,
                    'name': p.name,
                    'category': p.category,
                    'price': float(p.price),
                    'stock': p.stock_quantity,
                    'description': p.description
                }
                for p in products[:50]
            ]
            
            return Response({
                'success': True,
                'products': results,
                'count': len(results)
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Search error: {e}")
            return Response({'success': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class GetProductView(APIView):
    """GET /api/products/{product_id}"""
    
    def get(self, request, product_id):
        """Get product details"""
        try:
            product = ProductModel.objects.get(product_id=product_id)
            
            return Response({
                'success': True,
                'product': {
                    'product_id': product.product_id,
                    'code': product.code,
                    'name': product.name,
                    'category': product.category,
                    'price': float(product.price),
                    'stock': product.stock_quantity,
                    'description': product.description,
                    'is_active': product.is_active,
                    'created_at': product.created_at.isoformat()
                }
            }, status=status.HTTP_200_OK)
        
        except ProductModel.DoesNotExist:
            return Response({'success': False, 'message': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            logger.error(f"Get product error: {e}")
            return Response({'success': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ListCategoriesView(APIView):
    """GET /api/products/categories"""
    
    def get(self, request):
        """List all product categories"""
        return Response({
            'success': True,
            'categories': [
                'PRESCRIPTION_DRUG',
                'OTC_DRUG',
                'SUPPLEMENT',
                'MEDICAL_DEVICE',
                'WELLNESS',
                'DIAGNOSTIC'
            ]
        }, status=status.HTTP_200_OK)


# ============ URL ROUTING ============

from django.urls import path

medical_catalog_urls = [
    path('products/search/', SearchProductsView.as_view(), name='search-products'),
    path('products/categories/', ListCategoriesView.as_view(), name='list-categories'),
    path('products/<str:product_id>/', GetProductView.as_view(), name='get-product'),
]
