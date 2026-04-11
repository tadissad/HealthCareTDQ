"""views.py – comment-rate-service"""
from django.db.models import Avg, Count
from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from .models import Review


class ReviewSerializer(ModelSerializer):
    class Meta:
        model  = Review
        fields = '__all__'


class ReviewListCreate(generics.ListCreateAPIView):
    """GET /reviews/ | POST /reviews/"""
    serializer_class = ReviewSerializer

    def get_queryset(self):
        qs = Review.objects.all()
        product_id  = self.request.query_params.get('product_id')
        customer_id = self.request.query_params.get('customer_id')
        if product_id:
            qs = qs.filter(product_id=product_id)
        if customer_id:
            qs = qs.filter(customer_id=customer_id)
        return qs


class ReviewDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset         = Review.objects.all()
    serializer_class = ReviewSerializer


class ReviewSummary(APIView):
    """
    GET /reviews/summary/?product_ids=1,2,3
    Trả về avg rating + count cho từng product_id.
    Dùng bởi api-gateway khi hiển thị danh sách sản phẩm.
    """
    def get(self, request):
        ids_str = request.query_params.get('product_ids', '')
        try:
            ids = [int(i) for i in ids_str.split(',') if i.strip()]
        except ValueError:
            return Response({'error': 'product_ids không hợp lệ'}, status=status.HTTP_400_BAD_REQUEST)

        result = {}
        for pid in ids:
            agg = Review.objects.filter(product_id=pid).aggregate(
                avg=Avg('rating'), count=Count('id')
            )
            result[str(pid)] = {
                'avg':   round(agg['avg'], 1) if agg['avg'] else None,
                'count': agg['count'],
            }
        return Response(result)


class HealthView(APIView):
    def get(self, request):
        return Response({'status': 'UP', 'service': 'comment-rate-service'})
