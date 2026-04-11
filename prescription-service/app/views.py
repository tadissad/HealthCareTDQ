"""views.py – cart-service"""
from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from .models import CartItem


class CartItemSerializer(ModelSerializer):
    class Meta:
        model  = CartItem
        fields = '__all__'


class CartView(APIView):
    """GET /carts/{customer_id}/ – Lấy toàn bộ giỏ hàng của khách hàng"""
    def get(self, request, customer_id):
        items = CartItem.objects.filter(customer_id=customer_id)
        return Response(CartItemSerializer(items, many=True).data)

    def delete(self, request, customer_id):
        """Xóa toàn bộ giỏ hàng sau khi đặt hàng"""
        CartItem.objects.filter(customer_id=customer_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CartItemCreate(APIView):
    """POST /cart-items/ – Thêm sản phẩm vào giỏ"""
    def post(self, request):
        serializer = CartItemSerializer(data=request.data)
        if serializer.is_valid():
            # Nếu đã có item này → cộng dồn số lượng
            existing = CartItem.objects.filter(
                customer_id=request.data.get('customer_id'),
                product_id=request.data.get('product_id'),
            ).first()
            if existing:
                existing.quantity += int(request.data.get('quantity', 1))
                existing.save()
                return Response(CartItemSerializer(existing).data, status=status.HTTP_200_OK)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CartItemDetail(APIView):
    """PATCH /cart-items/{id}/ | DELETE /cart-items/{id}/"""
    def get_object(self, pk):
        try:
            return CartItem.objects.get(pk=pk)
        except CartItem.DoesNotExist:
            return None

    def patch(self, request, pk):
        item = self.get_object(pk)
        if not item:
            return Response({'error': 'Không tìm thấy'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CartItemSerializer(item, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        item = self.get_object(pk)
        if not item:
            return Response({'error': 'Không tìm thấy'}, status=status.HTTP_404_NOT_FOUND)
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class HealthView(APIView):
    def get(self, request):
        return Response({'status': 'UP', 'service': 'cart-service'})
