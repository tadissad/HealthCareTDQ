"""
Patient Domain Package

Contains all domain logic for the Patient bounded context.
Including entities, value objects, domain services, events, and repositories.
"""

from .entities import Patient, Doctor, MedicalRecord
from .value_objects import (
    PatientId, Email, Phone, Insurance, Address, BloodType, Money
)
from .events import (
    PatientRegistered, InsuranceUpdated, PatientContactUpdated,
    PatientDeactivated, MedicalRecordAdded
)
from .repositories import IPatientRepository
from .domain_services import (
    PatientRegistrationService, PatientContactUpdateService,
    PatientAddressUpdateService
)

__all__ = [
    "Patient", "Doctor", "MedicalRecord",
    "PatientId", "Email", "Phone", "Insurance", "Address", "BloodType", "Money",
    "PatientRegistered", "InsuranceUpdated", "PatientContactUpdated",
    "PatientDeactivated", "MedicalRecordAdded",
    "IPatientRepository",
    "PatientRegistrationService", "PatientContactUpdateService",
    "PatientAddressUpdateService",
]
