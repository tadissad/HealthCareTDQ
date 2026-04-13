"""Tao tai khoan admin lan dau (username admin, mat khau 123) neu chua co."""
from django.core.management.base import BaseCommand

from app.models import Account
from app.views import hash_password


class Command(BaseCommand):
    help = 'Ensure admin account exists (admin / 123) on first run only; does not reset password if admin already exists.'

    def handle(self, *args, **options):
        obj, created = Account.objects.get_or_create(
            username='admin',
            defaults={
                'password': hash_password('123'),
                'fullname': 'Quản trị viên',
                'role': 'admin',
                'is_active': True,
            },
        )
        if not created:
            dirty = False
            if obj.role != 'admin':
                obj.role = 'admin'
                dirty = True
            if not obj.is_active:
                obj.is_active = True
                dirty = True
            if dirty:
                obj.save(update_fields=['role', 'is_active'])
            self.stdout.write(self.style.SUCCESS('Admin account already exists (password unchanged).'))
        else:
            self.stdout.write(self.style.SUCCESS('Created admin: admin / 123'))
