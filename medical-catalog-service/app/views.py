from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import MedicalCategory, SubCategory
from .serializers import MedicalCategorySerializer, SubCategorySerializer


class CategoryListCreate(generics.ListCreateAPIView):
    queryset         = MedicalCategory.objects.filter(is_active=True)
    serializer_class = MedicalCategorySerializer


class CategoryDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset         = MedicalCategory.objects.all()
    serializer_class = MedicalCategorySerializer


class SubCategoryListCreate(generics.ListCreateAPIView):
    serializer_class = SubCategorySerializer

    def get_queryset(self):
        qs = SubCategory.objects.filter(is_active=True)
        parent = self.request.query_params.get('parent')
        if parent:
            qs = qs.filter(parent_id=parent)
        return qs


class HealthView(APIView):
    def get(self, request):
        return Response({'status': 'UP', 'service': 'catalog-service'})
