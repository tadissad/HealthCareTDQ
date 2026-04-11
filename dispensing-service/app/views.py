"""views.py – dispensing-service (formerly order-service)"""
import requests
from django.conf import settings
from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from .models import Order, OrderItem

PRESCRIPTION_SERVICE_URL = getattr(settings, 'PRESCRIPTION_SERVICE_URL', 'http://prescription-service:8000')
PATIENT_SERVICE_URL      = getattr(settings, 'PATIENT_SERVICE_URL',      'http://patient-service:8000')
PHARMACY_SERVICE_URL     = getattr(settings, 'PHARMACY_SERVICE_URL',     'http://pharmacy-service:8000')


class OrderItemSerializer(ModelSerializer):
    class Meta:
        model  = OrderItem
        fields = ['id', 'product_id', 'name', 'price', 'quantity']


class OrderSerializer(ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model  = Order
        fields = '__all__'


class OrderListCreate(generics.ListAPIView):
    """GET /orders/ – Danh sách đơn hàng với filter ?customer_id=, ?status="""
    serializer_class = OrderSerializer

    def get_queryset(self):
        qs = Order.objects.all()
        customer_id = self.request.query_params.get('customer_id')
        order_status = self.request.query_params.get('status')
        if customer_id:
            qs = qs.filter(customer_id=customer_id)
        if order_status:
            qs = qs.filter(status=order_status)
        return qs


class OrderDetail(APIView):
    """GET/PATCH /orders/{id}/"""
    def get_object(self, pk):
        try:
            return Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return None

    def get(self, request, pk):
        order = self.get_object(pk)
        if not order:
            return Response({'error': 'Không tìm thấy đơn hàng'}, status=status.HTTP_404_NOT_FOUND)
        return Response(OrderSerializer(order).data)

    def patch(self, request, pk):
        order = self.get_object(pk)
        if not order:
            return Response({'error': 'Không tìm thấy đơn hàng'}, status=status.HTTP_404_NOT_FOUND)
        new_status = request.data.get('status')
        if new_status:
            order.status = new_status
        note = request.data.get('note')
        if note:
            order.note = note
        order.save()
        return Response(OrderSerializer(order).data)


class OrderCreate(APIView):
    """
    POST /orders/create/
    Tạo phiếu xuất thuốc (dispensing) từ đơn thuốc tạm thời của bệnh nhân.
    Gọi prescription-service lấy items, tính tổng tiền, rồi xóa đơn thuốc tạm thời.
    """
    def post(self, request):
        customer_id      = request.data.get('customer_id')
        payment_method   = request.data.get('payment_method', 'Cash')
        shipping_method  = request.data.get('shipping_method', 'Standard')
        shipping_address = request.data.get('shipping_address', '')
        discount_rate    = float(request.data.get('discount_rate', 0))
        note             = request.data.get('note', '')

        if not customer_id:
            return Response({'error': 'Thiếu customer_id'}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Lấy đơn thuốc tạm thời từ prescription-service
        try:
            cart_r = requests.get(f"{PRESCRIPTION_SERVICE_URL}/carts/{customer_id}/", timeout=8)
            cart_items = cart_r.json() if cart_r.status_code == 200 else []
        except Exception as e:
            return Response({'error': f'Không thể kết nối prescription-service: {e}'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        if not cart_items:
            return Response({'error': 'Giỏ hàng trống'}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Lấy thông tin giá từ pharmacy-service (cart chỉ lưu product_id + quantity)
        product_cache = {}
        try:
            prod_r = requests.get(f"{PHARMACY_SERVICE_URL}/products/", timeout=8)
            if prod_r.status_code == 200:
                for p in prod_r.json():
                    product_cache[str(p['id'])] = {
                        'price': float(p.get('price', 0)),
                        'name':  p.get('name', f"Sản phẩm #{p['id']}"),
                        'stock_quantity': int(p.get('stock_quantity', 0)),
                    }
        except Exception:
            pass  # Tiếp tục, sẽ fallback về price=0 nếu không lấy được

        # 3. Kiểm tra tồn kho trước
        for item in cart_items:
            pid   = str(item.get('product_id', ''))
            info  = product_cache.get(pid, {})
            qty   = int(item.get('quantity', 1))
            stock = info.get('stock_quantity', 0)
            if stock < qty:
                return Response({'error': f"Sản phẩm '{info.get('name', 'ID:'+pid)}' đã hết hoặc không đủ số lượng."}, status=status.HTTP_400_BAD_REQUEST)

        # 4. Tạo Order
        order = Order.objects.create(
            customer_id=customer_id,
            payment_method=payment_method,
            shipping_method=shipping_method,
            shipping_address=shipping_address,
            discount_rate=discount_rate,
            note=note,
            status='Pending',
        )

        total = 0
        for item in cart_items:
            pid   = str(item.get('product_id', ''))
            info  = product_cache.get(pid, {})
            price = info.get('price', float(item.get('price', 0)))
            qty   = int(item.get('quantity', 1))
            name  = info.get('name', item.get('name', f"Sản phẩm #{pid}"))
            
            OrderItem.objects.create(
                order=order,
                product_id=item.get('product_id'),
                name=name,
                price=price,
                quantity=qty,
            )
            total += price * qty

            # Trừ tồn kho
            new_stock = info.get('stock_quantity', 0) - qty
            try:
                requests.patch(f"{PHARMACY_SERVICE_URL}/products/{pid}/", json={'stock_quantity': new_stock}, timeout=5)
            except Exception:
                pass # Lỗi tạm thì bỏ qua

        # 5. Áp dụng giảm giá và lưu tổng tiền
        order.total_amount = total * (1 - discount_rate)
        order.status = 'Paid'
        order.save()

        # 4. Xóa đơn thuốc tạm thời sau khi đã tạo phiếu xuất
        try:
            requests.delete(f"{PRESCRIPTION_SERVICE_URL}/carts/{customer_id}/", timeout=5)
        except Exception:
            pass  # Không block nếu prescription-service lỗi

        # 5. Cập nhật total_spent trong patient-service
        try:
            requests.put(
                f"{PATIENT_SERVICE_URL}/customers/by-account/{customer_id}/membership/",
                json={'increment_spent': order.total_amount},
                timeout=5
            )
        except Exception:
            pass

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class HealthView(APIView):
    def get(self, request):
        return Response({'status': 'UP', 'service': 'dispensing-service'})
