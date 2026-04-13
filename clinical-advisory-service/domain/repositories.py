"""
Clinical-Advisory Service Domain Layer - Repository Interface
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from .value_objects import ConsultationId, PatientId
from .entities import Consultation


class IClinicalConsultationRepository(ABC):
    """Repository interface for clinical consultations"""
    
    @abstractmethod
    def add(self, consultation: Consultation) -> None:
        """Add new consultation to repository"""
        pass
    
    @abstractmethod
    def update(self, consultation: Consultation) -> None:
        """Update existing consultation"""
        pass
    
    @abstractmethod
    def remove(self, consultation_id: ConsultationId) -> None:
        """Remove consultation from repository"""
        pass
    
    @abstractmethod
    def get_by_id(self, consultation_id: ConsultationId) -> Optional[Consultation]:
        """Get consultation by ID"""
        pass
    
    @abstractmethod
    def get_by_patient_id(self, patient_id: PatientId) -> List[Consultation]:
        """Get all consultations for a patient"""
        pass
    
    @abstractmethod
    def list_active_consultations(self) -> List[Consultation]:
        """List all active consultations"""
        pass
    
    @abstractmethod
    def list_pending_clinician_review(self) -> List[Consultation]:
        """List consultations awaiting clinician review"""
        pass
    
    @abstractmethod
    def list_urgent_cases(self) -> List[Consultation]:
        """List all urgent/emergency case consultations"""
        pass
    
    @abstractmethod
    def search_by_status(self, status: str) -> List[Consultation]:
        """Search consultations by status"""
        pass
    
    @abstractmethod
    def list_recent(self, days: int = 7) -> List[Consultation]:
        """List recently created/updated consultations"""
        pass
    
    @abstractmethod
    def list_all(self) -> List[Consultation]:
        """List all consultations"""
        pass
