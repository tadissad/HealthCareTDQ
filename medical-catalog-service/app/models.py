"""models.py – catalog-service: Phân cấp danh mục thuốc"""
from django.db import models


class MedicalCategory(models.Model):
    """Nhóm thuốc cấp cao (ví dụ: Thuốc tim mạch, Thuốc tiêu hóa)"""
    name        = models.CharField(max_length=255, unique=True, verbose_name="Tên nhóm")
    code        = models.CharField(max_length=50,  unique=True, verbose_name="Mã nhóm")
    description = models.TextField(blank=True, verbose_name="Mô tả")
    icon        = models.CharField(max_length=10, blank=True, verbose_name="Icon emoji")
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Danh mục thuốc"
        verbose_name_plural = "Danh mục thuốc"

    def __str__(self):
        return f"{self.icon} {self.name} ({self.code})"


class SubCategory(models.Model):
    """Phân nhóm thuốc cấp 2 (ví dụ: PPI, H2 Blocker trong nhóm Tiêu hóa)"""
    parent      = models.ForeignKey(
        MedicalCategory, on_delete=models.CASCADE,
        related_name='subcategories', verbose_name="Nhóm cha"
    )
    name        = models.CharField(max_length=255, verbose_name="Tên phân nhóm")
    code        = models.CharField(max_length=50,  verbose_name="Mã phân nhóm")
    description = models.TextField(blank=True, verbose_name="Mô tả lâm sàng")
    # Link đến product-service (lưu ID ngoài, không dùng FK xuyên service)
    product_ids = models.JSONField(default=list, verbose_name="Danh sách ID sản phẩm")
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['parent', 'name']
        unique_together = [('parent', 'code')]
        verbose_name = "Phân nhóm thuốc"

    def __str__(self):
        return f"{self.parent.name} > {self.name}"
