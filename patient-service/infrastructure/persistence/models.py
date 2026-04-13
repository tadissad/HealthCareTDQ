"""
Patient Infrastructure - ORM Models (Django)

These models are used ONLY for persistence with the database.
They are NOT domain entities - they are a technical mapping to the database schema.

Domain entities and models are intentionally separate to maintain clean architecture.
"""

from django.db import models


class PatientModel(models.Model):
    """ORM Model for Patient persistence"""
    
    # Identity
    patient_id = models.CharField(max_length=100, primary_key=True)
    account_id = models.CharField(max_length=100, unique=True, db_index=True)
    
    # Personal Information
    full_name = models.CharField(max_length=200)
    email = models.EmailField(db_index=True)
    phone = models.CharField(max_length=20, db_index=True)
    date_of_birth = models.DateTimeField()
    gender = models.CharField(max_length=10)  # Male, Female, Other
    blood_type = models.CharField(max_length=5, null=True, blank=True)
    
    # Address
    street = models.CharField(max_length=255, null=True, blank=True)
    ward = models.CharField(max_length=100, null=True, blank=True)
    district = models.CharField(max_length=100, null=True, blank=True)
    province = models.CharField(max_length=100, null=True, blank=True)
    postal_code = models.CharField(max_length=20, null=True, blank=True)
    
    # Insurance (BHYT - Bảo Hiểm Y Tế)
    insurance_code = models.CharField(max_length=50, null=True, blank=True)
    insurance_discount_rate = models.FloatField(default=0.0)
    insurance_valid_until = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "patients"
        indexes = [
            models.Index(fields=['account_id']),
            models.Index(fields=['email']),
            models.Index(fields=['phone']),
        ]
    
    def __str__(self):
        return f"Patient({self.patient_id}) - {self.full_name}"


class MedicalRecordModel(models.Model):
    """ORM Model for Medical Records"""
    
    record_id = models.CharField(max_length=100, primary_key=True)
    patient = models.ForeignKey(
        PatientModel,
        on_delete=models.CASCADE,
        related_name='medical_records',
        to_field='patient_id'
    )
    
    visit_date = models.DateTimeField()
    diagnosis = models.TextField()
    notes = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "medical_records"
        indexes = [
            models.Index(fields=['patient', 'visit_date']),
        ]
    
    def __str__(self):
        return f"MedicalRecord({self.record_id}) - {self.patient.full_name}"
