"""
views.py – customer-service
============================
Quản lý hồ sơ bệnh nhân / khách hàng y tế.

Endpoints:
  GET/POST  /customers/                           – Danh sách & tạo mới
  GET/PUT   /customers/{id}/                      – Chi tiết & cập nhật
  GET/PUT   /customers/by-account/{account_id}/  – Tra cứu qua account_id (dùng bởi api-gateway)
  PUT       /customers/by-account/{id}/membership/ – Cập nhật hạng thành viên
  GET       /health/                              – Health check
"""
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.response import Response

from .models import Customer
from .serializers import CustomerSerializer


class CustomerListCreate(generics.ListCreateAPIView):
    """GET /customers/ | POST /customers/"""
    queryset         = Customer.objects.all()
    serializer_class = CustomerSerializer


class CustomerDetail(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/PATCH/DELETE /customers/{id}/"""
    queryset         = Customer.objects.all()
    serializer_class = CustomerSerializer


class CustomerByAccount(APIView):
    """
    GET /customers/by-account/{account_id}/ – Lấy hồ sơ theo account_id
    PUT /customers/by-account/{account_id}/ – Cập nhật hồ sơ theo account_id
    """
    def get(self, request, account_id):
        try:
            customer = Customer.objects.get(account_id=account_id)
        except Customer.DoesNotExist:
            return Response({'error': 'Không tìm thấy hồ sơ khách hàng'}, status=status.HTTP_404_NOT_FOUND)
        return Response(CustomerSerializer(customer).data)

    def put(self, request, account_id):
        try:
            customer = Customer.objects.get(account_id=account_id)
        except Customer.DoesNotExist:
            # Auto-create nếu chưa có (tương thích với api-gateway)
            data = {**request.data, 'account_id': account_id}
            serializer = CustomerSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer = CustomerSerializer(customer, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, account_id):
        """POST: Tạo hồ sơ nếu chưa có"""
        data = {**request.data, 'account_id': account_id}
        serializer = CustomerSerializer(data=data)
        if serializer.is_valid():
            obj, created = Customer.objects.get_or_create(
                account_id=account_id,
                defaults=serializer.validated_data,
            )
            return Response(
                CustomerSerializer(obj).data,
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomerMembership(APIView):
    """
    PUT /customers/by-account/{account_id}/membership/
    Cập nhật hạng thành viên và tổng chi tiêu. Gọi từ order-service sau khi thanh toán.
    """
    def put(self, request, account_id):
        try:
            customer = Customer.objects.get(account_id=account_id)
        except Customer.DoesNotExist:
            return Response({'error': 'Không tìm thấy khách hàng'}, status=status.HTTP_404_NOT_FOUND)

        membership  = request.data.get('membership')
        total_spent = request.data.get('total_spent')

        if membership:
            customer.membership = membership
        if total_spent is not None:
            customer.total_spent = float(total_spent)
            customer.update_membership()   # auto-upgrade dựa trên chi tiêu

        customer.save()
        return Response(CustomerSerializer(customer).data)


class HealthView(APIView):
    def get(self, request):
        return Response({'status': 'UP', 'service': 'customer-service'})
