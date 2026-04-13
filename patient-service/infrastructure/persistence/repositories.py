"""
Patient Infrastructure - Repository Implementation

The repository is the bridge between the domain layer and persistence.
It implements the IPatientRepository interface using Django ORM.

This keeps the domain layer independent of any persistence technology.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from typing import Optional, List
from datetime import datetime

from ...domain import (
    Patient, PatientId, Email, Phone, Insurance, Address, BloodType, Money,
    MedicalRecord, IPatientRepository
)
from .models import PatientModel, MedicalRecordModel


class PatientRepositoryImpl(IPatientRepository):
    """
    Concrete implementation of IPatientRepository using Django ORM
    
    Responsibilities:
    - Load Patient aggregates from database
    - Save Patient aggregates to database
    - Transform between ORM models and domain entities
    """
    
    def add(self, patient: Patient) -> None:
        """Save a new patient to database"""
        PatientModel.objects.create(
            patient_id=str(patient._id),
            account_id=patient.account_id,
            full_name=patient.full_name,
            email=patient.email.value,
            phone=patient.phone.value,
            date_of_birth=patient.date_of_birth,
            gender=patient.gender,
            blood_type=patient.blood_type.value if patient.blood_type else None,
            street=patient.address.street if patient.address else None,
            ward=patient.address.ward if patient.address else None,
            district=patient.address.district if patient.address else None,
            province=patient.address.province if patient.address else None,
            postal_code=patient.address.postal_code if patient.address else None,
            insurance_code=patient.insurance.code if patient.insurance else None,
            insurance_discount_rate=patient.insurance.discount_rate if patient.insurance else 0,
            insurance_valid_until=patient.insurance.valid_until if patient.insurance else None,
        )
    
    def update(self, patient: Patient) -> None:
        """Update an existing patient in database"""
        PatientModel.objects.filter(patient_id=str(patient._id)).update(
            full_name=patient.full_name,
            email=patient.email.value,
            phone=patient.phone.value,
            gender=patient.gender,
            blood_type=patient.blood_type.value if patient.blood_type else None,
            street=patient.address.street if patient.address else None,
            ward=patient.address.ward if patient.address else None,
            district=patient.address.district if patient.address else None,
            province=patient.address.province if patient.address else None,
            postal_code=patient.address.postal_code if patient.address else None,
            insurance_code=patient.insurance.code if patient.insurance else None,
            insurance_discount_rate=patient.insurance.discount_rate if patient.insurance else 0,
            insurance_valid_until=patient.insurance.valid_until if patient.insurance else None,
            updated_at=datetime.now(),
        )
    
    def remove(self, patient: Patient) -> None:
        """Delete a patient from database"""
        PatientModel.objects.filter(patient_id=str(patient._id)).delete()
    
    def get_by_id(self, patient_id: PatientId) -> Optional[Patient]:
        """Retrieve patient by ID and reconstruct the aggregate"""
        try:
            model = PatientModel.objects.get(patient_id=str(patient_id))
            return self._model_to_entity(model)
        except PatientModel.DoesNotExist:
            return None
    
    def get_by_account_id(self, account_id: str) -> Optional[Patient]:
        """Retrieve patient by account ID"""
        try:
            model = PatientModel.objects.get(account_id=account_id)
            return self._model_to_entity(model)
        except PatientModel.DoesNotExist:
            return None
    
    def list_all(self) -> List[Patient]:
        """Get all patients"""
        models = PatientModel.objects.all()
        return [self._model_to_entity(m) for m in models]
    
    def list_by_email(self, email: str) -> List[Patient]:
        """Find patients by email"""
        models = PatientModel.objects.filter(email__iexact=email)
        return [self._model_to_entity(m) for m in models]
    
    def list_insured_patients(self) -> List[Patient]:
        """Get all patients with valid insurance"""
        models = PatientModel.objects.filter(
            insurance_code__isnull=False,
            insurance_valid_until__gte=datetime.now()
        )
        return [self._model_to_entity(m) for m in models]
    
    @staticmethod
    def _model_to_entity(model: PatientModel) -> Patient:
        """
        Transform ORM Model to Domain Entity
        
        This method reconstructs a Patient aggregate from database record.
        It creates all value objects and child entities.
        """
        
        # Create value objects
        patient_id = PatientId(model.patient_id)
        email = Email(model.email)
        phone = Phone(model.phone)
        
        blood_type = None
        if model.blood_type:
            blood_type = BloodType(model.blood_type)
        
        address = None
        if model.street or model.ward or model.district or model.province:
            address = Address(
                street=model.street or "",
                ward=model.ward or "",
                district=model.district or "",
                province=model.province or "",
                postal_code=model.postal_code or "",
            )
        
        insurance = None
        if model.insurance_code and model.insurance_valid_until:
            insurance = Insurance(
                code=model.insurance_code,
                discount_rate=model.insurance_discount_rate,
                valid_until=model.insurance_valid_until,
            )
        
        # Create aggregate
        patient = Patient(
            id=patient_id,
            account_id=model.account_id,
            full_name=model.full_name,
            email=email,
            phone=phone,
            date_of_birth=model.date_of_birth,
            gender=model.gender,
            blood_type=blood_type,
            address=address,
            insurance=insurance,
        )
        
        # Load medical records
        medical_record_models = MedicalRecordModel.objects.filter(patient_id=model.patient_id)
        for record_model in medical_record_models:
            record = MedicalRecord(
                id=record_model.record_id,
                patient_id=patient_id,
                visit_date=record_model.visit_date,
                diagnosis=record_model.diagnosis,
                notes=record_model.notes,
            )
            patient.add_medical_record(record)
        
        # Clear events since this is loaded from database, not newly created
        patient.clear_events()
        
        return patient
