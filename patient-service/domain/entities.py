"""
Patient Domain - Entities and Aggregates
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))
from shared_ddd.base import Aggregate, Entity, DomainEvent
from .value_objects import PatientId, Email, Phone, Insurance, Address, BloodType, Money
from .events import PatientRegistered, InsuranceUpdated, PatientContactUpdated


class Doctor(Entity):
    """Doctor entity - belongs to Patient aggregate"""
    
    def __init__(self, id: str, name: str, specialization: str):
        super().__init__(id)
        self.name = name
        self.specialization = specialization


class MedicalRecord(Entity):
    """Medical record - one record per patient visit"""
    
    def __init__(
        self,
        id: str,
        patient_id: PatientId,
        visit_date: datetime,
        diagnosis: str,
        notes: Optional[str] = None,
    ):
        super().__init__(id)
        self.patient_id = patient_id
        self.visit_date = visit_date
        self.diagnosis = diagnosis
        self.notes = notes


class Patient(Aggregate):
    """
    Patient Aggregate Root
    
    Represents a patient in the healthcare system.
    Contains all information related to a patient.
    """
    
    def __init__(
        self,
        id: PatientId,
        account_id: str,
        full_name: str,
        email: Email,
        phone: Phone,
        date_of_birth: datetime,
        gender: str,
        blood_type: Optional[BloodType] = None,
        address: Optional[Address] = None,
        insurance: Optional[Insurance] = None,
    ):
        super().__init__(id)
        
        # Identity
        self._id = id
        self.account_id = account_id
        
        # Personal information
        self.full_name = full_name
        self.email = email
        self.phone = phone
        self.date_of_birth = date_of_birth
        self.gender = gender
        self.blood_type = blood_type
        self.address = address
        
        # Insurance
        self.insurance = insurance
        
        # Metadata
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        
        # Child entities
        self.medical_records: List[MedicalRecord] = []
        
        # Raise domain event
        self.add_event(
            PatientRegistered(
                aggregate_id=str(id),
                patient_id=str(id),
                account_id=account_id,
                name=full_name,
                email=email.value,
                occurred_at=self.created_at,
            )
        )
    
    def update_contact_info(self, email: Email, phone: Phone) -> None:
        """Update patient's contact information"""
        old_email = self.email
        old_phone = self.phone
        
        self.email = email
        self.phone = phone
        self.updated_at = datetime.now()
        
        self.add_event(
            PatientContactUpdated(
                aggregate_id=str(self._id),
                patient_id=str(self._id),
                old_email=old_email.value,
                new_email=email.value,
                old_phone=old_phone.value,
                new_phone=phone.value,
                occurred_at=self.updated_at,
            )
        )
    
    def update_address(self, address: Address) -> None:
        """Update patient's address"""
        self.address = address
        self.updated_at = datetime.now()
    
    def register_insurance(self, insurance: Insurance) -> None:
        """Register or update patient's insurance"""
        if not insurance.is_valid():
            raise ValueError("Insurance is expired")
        
        old_insurance = self.insurance
        self.insurance = insurance
        self.updated_at = datetime.now()
        
        self.add_event(
            InsuranceUpdated(
                aggregate_id=str(self._id),
                patient_id=str(self._id),
                insurance_code=insurance.code,
                discount_rate=insurance.discount_rate,
                valid_until=insurance.valid_until,
                old_insurance_code=old_insurance.code if old_insurance else None,
                occurred_at=self.updated_at,
            )
        )
    
    def add_medical_record(self, record: MedicalRecord) -> None:
        """Add a medical record to patient's history"""
        self.medical_records.append(record)
        self.updated_at = datetime.now()
    
    def is_insured(self) -> bool:
        """Check if patient has valid insurance"""
        return self.insurance is not None and self.insurance.is_valid()
    
    def get_age(self) -> int:
        """Calculate patient's age"""
        today = datetime.now()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    def calculate_treatment_cost(self, base_cost: Money) -> dict:
        """Calculate treatment cost with insurance discount"""
        if not self.is_insured():
            return {
                "base_cost": base_cost.amount,
                "discount": 0,
                "patient_payment": base_cost.amount,
                "insurance_payment": 0,
            }
        
        insurance_payment = self.insurance.calculate_insured_amount(base_cost.amount)
        patient_payment = self.insurance.calculate_patient_payment(base_cost.amount)
        
        return {
            "base_cost": base_cost.amount,
            "discount": insurance_payment,
            "patient_payment": patient_payment,
            "insurance_payment": insurance_payment,
        }
