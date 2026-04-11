"""models.py – cart-service"""
from django.db import models


class CartItem(models.Model):
    """
    Một mục trong giỏ hàng.
    Không có model Cart riêng: giỏ hàng = tất cả CartItem của một customer_id.
    """
    customer_id = models.IntegerField(db_index=True, verbose_name="ID khách hàng")
    product_id  = models.IntegerField(verbose_name="ID sản phẩm y tế")
    quantity    = models.IntegerField(default=1, verbose_name="Số lượng")
    added_at    = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-added_at']
        verbose_name = "Mục giỏ hàng"

    def __str__(self):
        return f"Customer {self.customer_id} – Product {self.product_id} × {self.quantity}"
