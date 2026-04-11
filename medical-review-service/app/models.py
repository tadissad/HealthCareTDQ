"""models.py – comment-rate-service"""
from django.db import models


class Review(models.Model):
    product_id  = models.IntegerField(db_index=True, verbose_name="ID sản phẩm")
    customer_id = models.IntegerField(db_index=True, verbose_name="ID khách hàng")
    rating      = models.IntegerField(choices=[(i, f"{i} sao") for i in range(1, 6)], verbose_name="Số sao")
    comment     = models.TextField(blank=True, verbose_name="Nhận xét")
    # Đánh giá chuyên sâu về thuốc
    effectiveness = models.IntegerField(
        choices=[(i, i) for i in range(1, 6)], null=True, blank=True,
        verbose_name="Hiệu quả điều trị (1-5)"
    )
    side_effect_experience = models.TextField(blank=True, verbose_name="Trải nghiệm tác dụng phụ")
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = [('product_id', 'customer_id')]
        verbose_name = "Đánh giá sản phẩm"

    def __str__(self):
        return f"Product {self.product_id} – ★{self.rating} by Customer {self.customer_id}"
