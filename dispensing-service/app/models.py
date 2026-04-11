"""models.py – order-service"""
from django.db import models


class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending',   'Chờ xác nhận'),
        ('Confirmed', 'Đã xác nhận'),
        ('Paid',      'Đã thanh toán'),
        ('Shipping',  'Đang giao hàng'),
        ('Delivered', 'Đã giao'),
        ('Cancelled', 'Đã hủy'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('Cash',         'Tiền mặt'),
        ('BankTransfer', 'Chuyển khoản'),
        ('MoMo',         'Ví MoMo'),
        ('VNPAY',        'VNPAY'),
        ('Insurance',    'Bảo hiểm y tế'),
    ]

    SHIPPING_CHOICES = [
        ('Standard', 'Giao hàng tiêu chuẩn (3-5 ngày)'),
        ('Express',  'Giao hàng nhanh (1-2 ngày)'),
        ('Pickup',   'Nhận tại nhà thuốc'),
    ]

    customer_id       = models.IntegerField(db_index=True, verbose_name="ID khách hàng")
    status            = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    payment_method    = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='Cash')
    shipping_method   = models.CharField(max_length=20, choices=SHIPPING_CHOICES, default='Standard')
    shipping_address  = models.TextField(blank=True, verbose_name="Địa chỉ giao hàng")
    total_amount      = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    discount_rate     = models.FloatField(default=0.0, verbose_name="Tỷ lệ giảm giá (0.0-1.0)")
    note              = models.TextField(blank=True, verbose_name="Ghi chú đơn thuốc")
    prescription_code = models.CharField(max_length=100, blank=True, verbose_name="Mã đơn thuốc")
    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Đơn hàng"

    def __str__(self):
        return f"Order #{self.id} – Customer {self.customer_id} – {self.status}"


class OrderItem(models.Model):
    """Chi tiết từng sản phẩm trong đơn hàng"""
    order      = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_id = models.IntegerField(verbose_name="ID sản phẩm")
    name       = models.CharField(max_length=255, verbose_name="Tên sản phẩm (snapshot)")
    price      = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Giá tại thời điểm mua")
    quantity   = models.IntegerField(default=1)

    def get_subtotal(self):
        return float(self.price) * self.quantity

    def __str__(self):
        return f"Order #{self.order_id} – {self.name} × {self.quantity}"
