from rest_framework import serializers
from .models import MedicalProduct


class MedicalProductSerializer(serializers.ModelSerializer):
    category_display    = serializers.CharField(source='get_category_display',   read_only=True)
    dosage_form_display = serializers.CharField(source='get_dosage_form_display', read_only=True)

    class Meta:
        model  = MedicalProduct
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
