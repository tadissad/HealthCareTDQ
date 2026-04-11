from rest_framework import serializers
from .models import MedicalCategory, SubCategory


class SubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model  = SubCategory
        fields = '__all__'


class MedicalCategorySerializer(serializers.ModelSerializer):
    subcategories = SubCategorySerializer(many=True, read_only=True)

    class Meta:
        model  = MedicalCategory
        fields = '__all__'
