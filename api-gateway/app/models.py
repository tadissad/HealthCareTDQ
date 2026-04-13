from django.db import models


class Account(models.Model):
    """
    Tài khoản người dùng lưu local tại api-gateway.
    Mật khẩu được hash bằng bcrypt/sha256.
    Liên kết với Customer profile qua customer_id (reference đến customer-service).
    """
    ROLE_CHOICES = [
        ('customer', 'Khách hàng'),
        ('manager',  'Quản lý nhà thuốc'),
        ('staff',    'Nhân viên (sản phẩm)'),
        ('admin',    'Quản trị viên'),
    ]

    username    = models.CharField(max_length=100, unique=True, verbose_name="Tên đăng nhập")
    password    = models.CharField(max_length=255, verbose_name="Mật khẩu (hashed)")
    fullname    = models.CharField(max_length=255, verbose_name="Họ tên đầy đủ")
    phone       = models.CharField(max_length=20, blank=True, verbose_name="Số điện thoại")
    email       = models.EmailField(blank=True, verbose_name="Email")
    address     = models.TextField(blank=True, verbose_name="Địa chỉ")
    role        = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Tài khoản"
        verbose_name_plural = "Tài khoản người dùng"

    def __str__(self):
        return f"[{self.role}] {self.username} – {self.fullname}"
