from django.contrib import admin
from .models import MedicalProduct

@admin.register(MedicalProduct)
class MedicalProductAdmin(admin.ModelAdmin):
    list_display  = ['name', 'generic_name', 'category', 'dosage_form', 'price', 'stock_quantity', 'requires_prescription']
    list_filter   = ['category', 'dosage_form', 'requires_prescription', 'is_active']
    search_fields = ['name', 'generic_name', 'manufacturer']
