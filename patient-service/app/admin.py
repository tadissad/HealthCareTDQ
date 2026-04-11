from django.contrib import admin
from .models import Customer

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'account_id', 'membership', 'total_spent', 'insurance_code']
    list_filter  = ['membership', 'blood_type']
    search_fields = ['name', 'insurance_code', 'phone']
