"""
views.py – product-service
===========================
CRUD API cho sản phẩm y tế / dược phẩm.
Hỗ trợ filter nâng cao theo nhóm thuốc, triệu chứng, tên hoạt chất.

Endpoints:
  GET    /products/          – Danh sách (filter: ?category=, ?q=, ?symptom=, ?prescription=)
  POST   /products/          – Thêm sản phẩm mới
  GET    /products/{id}/     – Chi tiết sản phẩm
  PUT    /products/{id}/     – Cập nhật toàn bộ (dùng bởi api-gateway khi trừ kho)
  PATCH  /products/{id}/     – Cập nhật một phần
  DELETE /products/{id}/     – Xóa sản phẩm
  GET    /health/            – Health check
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status

from .models import MedicalProduct
from .serializers import MedicalProductSerializer


class ProductListCreate(APIView):
    """
    GET  /products/ – Danh sách sản phẩm y tế với filter nâng cao
    POST /products/ – Thêm sản phẩm mới
    """

    def get(self, request):
        qs = MedicalProduct.objects.filter(is_active=True)

        # Filter theo nhóm thuốc
        category = request.query_params.get('category')
        if category:
            qs = qs.filter(category=category)

        # Filter theo từ khóa tên thương mại / hoạt chất
        q = request.query_params.get('q', '').strip()
        if q:
            qs = qs.filter(name__icontains=q) | qs.filter(generic_name__icontains=q)

        # Filter theo triệu chứng (symptom_tags JSON field)
        symptom = request.query_params.get('symptom', '').strip()
        if symptom:
            qs = qs.filter(symptom_tags__contains=symptom)

        # Filter theo cần kê đơn
        prescription = request.query_params.get('prescription')
        if prescription is not None:
            qs = qs.filter(requires_prescription=(prescription.lower() == 'true'))

        serializer = MedicalProductSerializer(qs, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = MedicalProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /products/{id}/ – Chi tiết
    PUT    /products/{id}/ – Cập nhật (trừ kho từ api-gateway)
    PATCH  /products/{id}/ – Cập nhật một phần
    DELETE /products/{id}/ – Xóa
    """
    queryset         = MedicalProduct.objects.all()
    serializer_class = MedicalProductSerializer


class HealthView(APIView):
    def get(self, request):
        total = MedicalProduct.objects.filter(is_active=True).count()
        return Response({
            'status':         'UP',
            'service':        'product-service',
            'active_products': total,
        })
