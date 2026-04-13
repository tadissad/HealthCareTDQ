"""
Patient Domain - Repository Interface
"""

from abc import ABC, abstractmethod
from typing import Optional, List

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))
from shared_ddd.base import IRepository
from .entities import Patient
from .value_objects import PatientId


class IPatientRepository(IRepository, ABC):
    """
    Repository interface for Patient aggregate
    
    Defines contracts for persistence without implementation details.
    Implementation can use Django ORM, SQL, NoSQL, or any other mechanism.
    """
    
    @abstractmethod
    def add(self, patient: Patient) -> None:
        """Save a new patient"""
        pass
    
    @abstractmethod
    def update(self, patient: Patient) -> None:
        """Update an existing patient"""
        pass
    
    @abstractmethod
    def remove(self, patient: Patient) -> None:
        """Remove a patient"""
        pass
    
    @abstractmethod
    def get_by_id(self, patient_id: PatientId) -> Optional[Patient]:
        """Get patient by patient ID"""
        pass
    
    @abstractmethod
    def get_by_account_id(self, account_id: str) -> Optional[Patient]:
        """Get patient by account ID (FK to auth service)"""
        pass
    
    @abstractmethod
    def list_all(self) -> List[Patient]:
        """Get all patients"""
        pass
    
    @abstractmethod
    def list_by_email(self, email: str) -> List[Patient]:
        """Find patients by email"""
        pass
    
    @abstractmethod
    def list_insured_patients(self) -> List[Patient]:
        """Get all patients with valid insurance"""
        pass
