from django.db import models


class Customer(models.Model):
    """
    Hồ sơ bệnh nhân / khách hàng y tế.
    Liên kết với Account trong api-gateway qua account_id.
    """
    MEMBERSHIP_CHOICES = [
        ('Bronze',   'Đồng'),
        ('Silver',   'Bạc'),
        ('Gold',     'Vàng'),
        ('Platinum', 'Bạch kim'),
    ]

    BLOOD_TYPE_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
        ('unknown', 'Chưa xác định'),
    ]

    account_id      = models.IntegerField(unique=True, verbose_name="ID tài khoản (api-gateway)")
    name            = models.CharField(max_length=255, verbose_name="Họ tên")
    email           = models.EmailField(blank=True, verbose_name="Email")
    phone           = models.CharField(max_length=20, blank=True, verbose_name="Số điện thoại")
    address         = models.TextField(blank=True, verbose_name="Địa chỉ")
    date_of_birth   = models.DateField(null=True, blank=True, verbose_name="Ngày sinh")
    blood_type      = models.CharField(
        max_length=10, choices=BLOOD_TYPE_CHOICES, default='unknown', verbose_name="Nhóm máu"
    )
    # Thông tin bảo hiểm y tế
    insurance_code  = models.CharField(max_length=50, blank=True, verbose_name="Mã BHYT")
    # Tiền sử bệnh (lưu dưới dạng JSON list)
    medical_history = models.JSONField(default=list, verbose_name="Tiền sử bệnh")
    # Dị ứng
    allergies       = models.JSONField(default=list, verbose_name="Dị ứng thuốc")
    # Hạng thành viên
    membership      = models.CharField(
        max_length=20, choices=MEMBERSHIP_CHOICES, default='Bronze', verbose_name="Hạng thành viên"
    )
    total_spent     = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name="Tổng chi tiêu (VND)"
    )
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Khách hàng"
        verbose_name_plural = "Danh sách khách hàng"

    def __str__(self):
        return f"[{self.membership}] {self.name} (account={self.account_id})"

    def update_membership(self):
        """Tự động cập nhật hạng thành viên dựa trên tổng chi tiêu."""
        spent = float(self.total_spent)
        if spent >= 10_000_000:
            self.membership = 'Platinum'
        elif spent >= 5_000_000:
            self.membership = 'Gold'
        elif spent >= 2_000_000:
            self.membership = 'Silver'
        else:
            self.membership = 'Bronze'
