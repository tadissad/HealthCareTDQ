"""Tao tai khoan staff lan dau (staff / 123) neu chua co; khong doi mat khau neu da ton tai."""
from django.core.management.base import BaseCommand

from app.models import Account
from app.views import hash_password


class Command(BaseCommand):
    help = 'Ensure staff account exists (staff / 123) on first run only; does not reset password if staff already exists.'

    def handle(self, *args, **options):
        obj, created = Account.objects.get_or_create(
            username='staff',
            defaults={
                'password': hash_password('123'),
                'fullname': 'Nhân viên sản phẩm',
                'role': 'staff',
                'is_active': True,
            },
        )
        if not created:
            dirty = False
            if obj.role != 'staff':
                obj.role = 'staff'
                dirty = True
            if not obj.is_active:
                obj.is_active = True
                dirty = True
            if dirty:
                obj.save(update_fields=['role', 'is_active'])
            self.stdout.write(self.style.SUCCESS('Staff account already exists (password unchanged).'))
        else:
            self.stdout.write(self.style.SUCCESS('Created staff: staff / 123'))
