"""
Patient Domain Events
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))
from shared_ddd.base import DomainEvent


@dataclass
class PatientRegistered(DomainEvent):
    """Event: Patient was registered in the system"""
    patient_id: str
    account_id: str
    name: str
    email: str
    event_type: str = "patient.registered"


@dataclass
class InsuranceUpdated(DomainEvent):
    """Event: Patient's insurance information was updated"""
    patient_id: str
    insurance_code: str
    discount_rate: float
    valid_until: datetime
    old_insurance_code: Optional[str] = None
    event_type: str = "patient.insurance_updated"


@dataclass
class PatientContactUpdated(DomainEvent):
    """Event: Patient's contact information was updated"""
    patient_id: str
    old_email: str
    new_email: str
    old_phone: str
    new_phone: str
    event_type: str = "patient.contact_updated"


@dataclass
class PatientDeactivated(DomainEvent):
    """Event: Patient account was deactivated"""
    patient_id: str
    reason: str
    event_type: str = "patient.deactivated"


@dataclass
class MedicalRecordAdded(DomainEvent):
    """Event: Medical record was added to patient"""
    patient_id: str
    record_id: str
    diagnosis: str
    visit_date: datetime
    event_type: str = "patient.medical_record_added"
