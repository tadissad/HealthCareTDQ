"""
models.py – product-service
============================
Model sản phẩm y tế / dược phẩm cho hệ thống Healthcare E-commerce.
Hỗ trợ phân loại chuyên sâu theo nhóm thuốc, dạng bào chế, và kê đơn.
"""
from django.db import models


class MedicalProduct(models.Model):
    """Sản phẩm y tế / dược phẩm"""

    CATEGORY_CHOICES = [
        ('ulcer_hp_support',        'Hỗ trợ Điều trị Viêm loét & HP'),
        ('reflux_heartburn',        'Giảm Trào ngược & Ợ chua'),
        ('probiotic_digestion',     'Men vi sinh & Hỗ trợ Tiêu hóa'),
        ('herbal_extract',          'Tinh chất Nghệ & Thảo dược'),
        ('stomach_nutrition',       'Thực phẩm & Dinh dưỡng Dạ dày'),
        ('equipment_device',        'Dụng cụ & Thiết bị Hỗ trợ'),
        ('test_kit_home',           'Bộ xét nghiệm & Kiểm tra tại nhà'),
        ('consultation_package',    'Gói khám & Tư vấn Bác sĩ'),
        ('elderly_weak_digestion',  'Dành cho Người già & Hệ tiêu hóa yếu'),
        ('vitamin_mineral',         'Vitamin & Khoáng chất Bổ trợ'),
    ]

    DOSAGE_FORM_CHOICES = [
        ('tablet',      'Viên nén'),
        ('capsule',     'Viên nang'),
        ('syrup',       'Siro'),
        ('suspension',  'Hỗn dịch uống'),
        ('sachet',      'Gói bột pha uống'),
        ('injection',   'Tiêm'),
        ('gel',         'Gel'),
        ('cream',       'Kem'),
        ('drops',       'Nhỏ giọt'),
    ]

    # ── Thông tin cơ bản ──────────────────────────────────────────────────────
    name             = models.CharField(max_length=255, verbose_name="Tên thương mại")
    generic_name     = models.CharField(max_length=255, blank=True, verbose_name="Tên hoạt chất")
    category         = models.CharField(
        max_length=50, choices=CATEGORY_CHOICES, default='other', verbose_name="Nhóm thuốc"
    )
    dosage_form      = models.CharField(
        max_length=50, choices=DOSAGE_FORM_CHOICES, default='tablet', verbose_name="Dạng bào chế"
    )
    dosage_strength  = models.CharField(max_length=100, blank=True, verbose_name="Hàm lượng")  # "20mg", "500mg/5ml"
    manufacturer     = models.CharField(max_length=255, blank=True, verbose_name="Hãng sản xuất")
    origin_country   = models.CharField(max_length=100, blank=True, verbose_name="Xuất xứ")

    # ── Giá & tồn kho ─────────────────────────────────────────────────────────
    price            = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Giá bán (VND)")
    unit             = models.CharField(max_length=50, default='hộp', verbose_name="Đơn vị")   # hộp, vỉ, chai
    stock_quantity   = models.IntegerField(default=0, verbose_name="Số lượng tồn kho")

    # ── Mô tả y tế ────────────────────────────────────────────────────────────
    description      = models.TextField(verbose_name="Công dụng / Chỉ định")
    side_effects     = models.TextField(blank=True, verbose_name="Tác dụng phụ")
    contraindications= models.TextField(blank=True, verbose_name="Chống chỉ định")
    usage_instruction= models.TextField(blank=True, verbose_name="Hướng dẫn sử dụng")

    # ── Phân loại bổ sung ─────────────────────────────────────────────────────
    requires_prescription = models.BooleanField(default=False, verbose_name="Cần kê đơn bác sĩ")
    # Tag triệu chứng: ["đau dạ dày", "ợ chua", "đầy bụng"]
    symptom_tags     = models.JSONField(default=list, blank=True, verbose_name="Tag triệu chứng")
    is_active        = models.BooleanField(default=True, verbose_name="Đang kinh doanh")

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-id']
        verbose_name = "Sản phẩm y tế"
        verbose_name_plural = "Danh sách sản phẩm y tế"

    def __str__(self):
        return f"[{self.get_category_display()}] {self.name} {self.dosage_strength} – {self.price:,} VND"
        verbose_name_plural = "Danh sách sản phẩm y tế"

    def __str__(self):
        return f"[{self.get_category_display()}] {self.name} {self.dosage_strength} – {self.price:,} VND"
