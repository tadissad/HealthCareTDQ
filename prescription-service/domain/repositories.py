"""
Prescription Service Domain Layer - Repository Interface
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from abc import ABC, abstractmethod
from typing import List, Optional

from shared_ddd.base import IRepository
from .value_objects import PrescriptionId, CustomerId, PrescriptionStatus
from .entities import Prescription


class IPrescriptionRepository(IRepository, ABC):
    """Interface for Prescription repository"""
    
    @abstractmethod
    def add(self, prescription: Prescription) -> None:
        """Persist new prescription"""
        pass
    
    @abstractmethod
    def update(self, prescription: Prescription) -> None:
        """Update existing prescription"""
        pass
    
    @abstractmethod
    def remove(self, prescription_id: PrescriptionId) -> None:
        """Delete prescription"""
        pass
    
    @abstractmethod
    def get_by_id(self, prescription_id: PrescriptionId) -> Optional[Prescription]:
        """Retrieve prescription by ID"""
        pass
    
    @abstractmethod
    def get_by_customer_id(self, customer_id: CustomerId) -> List[Prescription]:
        """Retrieve all prescriptions for customer"""
        pass
    
    @abstractmethod
    def list_by_status(self, status: PrescriptionStatus) -> List[Prescription]:
        """Retrieve prescriptions by status"""
        pass
    
    @abstractmethod
    def list_draft_prescriptions(self) -> List[Prescription]:
        """Retrieve draft prescriptions"""
        pass
    
    @abstractmethod
    def list_submitted_prescriptions(self) -> List[Prescription]:
        """Retrieve submitted prescriptions"""
        pass
    
    @abstractmethod
    def list_active_prescriptions(self) -> List[Prescription]:
        """Retrieve active (non-cancelled) prescriptions"""
        pass
    
    @abstractmethod
    def list_all(self) -> List[Prescription]:
        """Retrieve all prescriptions"""
        pass
    
    @abstractmethod
    def search_by_customer_and_status(self, customer_id: CustomerId, status: PrescriptionStatus) -> List[Prescription]:
        """Retrieve prescriptions by customer and status"""
        pass
    
    @abstractmethod
    def list_recent(self, limit: int = 10) -> List[Prescription]:
        """Retrieve most recent prescriptions"""
        pass
