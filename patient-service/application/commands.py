"""
Patient Application Layer - Commands

Commands represent actions/requests that modify the state of the system.
They are immutable DTOs that capture user intent.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class RegisterPatientCommand:
    """Command: Register a new patient"""
    account_id: str
    full_name: str
    email: str
    phone: str
    date_of_birth: datetime
    gender: str  # Male, Female, Other
    blood_type: Optional[str] = None


@dataclass
class UpdatePatientInsuranceCommand:
    """Command: Update patient's insurance"""
    patient_id: str
    insurance_code: str
    discount_rate: float = 0.8
    valid_days: int = 365


@dataclass
class UpdatePatientContactCommand:
    """Command: Update patient's contact information"""
    patient_id: str
    email: Optional[str] = None
    phone: Optional[str] = None


@dataclass
class UpdatePatientAddressCommand:
    """Command: Update patient's address"""
    patient_id: str
    street: str
    ward: str
    district: str
    province: str
    postal_code: str


@dataclass
class DeactivatePatientCommand:
    """Command: Deactivate patient account"""
    patient_id: str
    reason: str
