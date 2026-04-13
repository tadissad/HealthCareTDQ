"""
Patient Domain Services
"""

from datetime import datetime, timedelta
from typing import Optional

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))
from shared_ddd.base import DomainService
from .entities import Patient
from .value_objects import (
    PatientId, Email, Phone, Insurance, Address, BloodType, Money
)
from .repositories import IPatientRepository


class PatientRegistrationService(DomainService):
    """
    Domain Service for patient registration and onboarding
    
    Handles complex business logic that involves multiple domain objects
    but doesn't belong to any single entity.
    """
    
    def __init__(self, patient_repo: IPatientRepository):
        self.patient_repo = patient_repo
    
    def execute(self, *args, **kwargs):
        """Abstract method - not used for domain services"""
        pass
    
    def register_new_patient(
        self,
        account_id: str,
        full_name: str,
        email: str,
        phone: str,
        date_of_birth: datetime,
        gender: str,
        blood_type: Optional[str] = None,
    ) -> Patient:
        """
        Register a new patient
        
        Creates a Patient aggregate and saves it.
        Domain events will be raised automatically.
        
        Args:
            account_id: Unique ID from auth service
            full_name: Patient's full name
            email: Patient's email
            phone: Patient's phone number
            date_of_birth: Patient's date of birth
            gender: Male, Female, Other
            blood_type: Optional blood type (O, A, B, AB, etc.)
        
        Returns:
            Newly created Patient aggregate
        
        Raises:
            InvalidValueObjectException: If any value object is invalid
        """
        # Generate unique patient ID
        timestamp = datetime.now().timestamp()
        patient_id = PatientId(f"PAT_{account_id}_{int(timestamp*1000)}")
        
        # Create value objects (validation happens in __post_init__)
        patient_email = Email(email)
        patient_phone = Phone(phone)
        
        patient_blood_type = None
        if blood_type:
            patient_blood_type = BloodType(blood_type)
        
        # Create the aggregate
        patient = Patient(
            id=patient_id,
            account_id=account_id,
            full_name=full_name,
            email=patient_email,
            phone=patient_phone,
            date_of_birth=date_of_birth,
            gender=gender,
            blood_type=patient_blood_type,
        )
        
        # Persist
        self.patient_repo.add(patient)
        
        return patient
    
    def issue_insurance(
        self,
        patient_id: PatientId,
        insurance_code: str,
        discount_rate: float = 0.8,
        valid_days: int = 365,
    ) -> None:
        """
        Issue or update patient's insurance
        
        Args:
            patient_id: ID of patient
            insurance_code: Insurance code (e.g., BHYT_2024_001)
            discount_rate: Discount rate (0.8 = 80% covered by insurance)
            valid_days: How many days until insurance expires
        
        Raises:
            ValueError: If patient not found
        """
        patient = self.patient_repo.get_by_id(patient_id)
        if not patient:
            raise ValueError(f"Patient {patient_id} not found")
        
        # Create insurance value object
        insurance = Insurance(
            code=insurance_code,
            discount_rate=discount_rate,
            valid_until=datetime.now() + timedelta(days=valid_days),
        )
        
        # Update patient aggregate
        patient.register_insurance(insurance)
        
        # Persist
        self.patient_repo.update(patient)


class PatientContactUpdateService(DomainService):
    """Domain Service for updating patient contact information"""
    
    def __init__(self, patient_repo: IPatientRepository):
        self.patient_repo = patient_repo
    
    def execute(self, *args, **kwargs):
        pass
    
    def update_contact(
        self,
        patient_id: PatientId,
        email: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> None:
        """
        Update patient's contact information
        
        Can update email, phone, or both.
        """
        patient = self.patient_repo.get_by_id(patient_id)
        if not patient:
            raise ValueError(f"Patient {patient_id} not found")
        
        # Only update if provided
        if email and phone:
            patient.update_contact_info(Email(email), Phone(phone))
        elif email:
            patient.update_contact_info(Email(email), patient.phone)
        elif phone:
            patient.update_contact_info(patient.email, Phone(phone))
        
        self.patient_repo.update(patient)


class PatientAddressUpdateService(DomainService):
    """Domain Service for updating patient address"""
    
    def __init__(self, patient_repo: IPatientRepository):
        self.patient_repo = patient_repo
    
    def execute(self, *args, **kwargs):
        pass
    
    def update_address(
        self,
        patient_id: PatientId,
        street: str,
        ward: str,
        district: str,
        province: str,
        postal_code: str,
    ) -> None:
        """Update patient's address"""
        patient = self.patient_repo.get_by_id(patient_id)
        if not patient:
            raise ValueError(f"Patient {patient_id} not found")
        
        address = Address(
            street=street,
            ward=ward,
            district=district,
            province=province,
            postal_code=postal_code,
        )
        
        patient.update_address(address)
        self.patient_repo.update(patient)
