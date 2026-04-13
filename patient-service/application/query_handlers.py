"""
Patient Application Layer - Query Handlers

Query handlers handle read-only operations (queries).
They return DTOs, not domain entities.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from .queries import (
    GetPatientByIdQuery, GetPatientByAccountIdQuery,
    GetPatientByEmailQuery, ListAllPatientsQuery,
    ListInsuredPatientsQuery, GetPatientMedicalRecordsQuery
)
from ..domain import PatientId, IPatientRepository


class GetPatientByIdQueryHandler:
    """Handle: GetPatientByIdQuery"""
    
    def __init__(self, patient_repo: IPatientRepository):
        self.patient_repo = patient_repo
    
    def handle(self, query: GetPatientByIdQuery) -> dict:
        """Get patient by ID - returns DTO"""
        try:
            patient = self.patient_repo.get_by_id(PatientId(query.patient_id))
            
            if not patient:
                return None
            
            return {
                "id": str(patient._id),
                "account_id": patient.account_id,
                "full_name": patient.full_name,
                "email": patient.email.value,
                "phone": patient.phone.value,
                "date_of_birth": patient.date_of_birth.isoformat(),
                "gender": patient.gender,
                "blood_type": patient.blood_type.value if patient.blood_type else None,
                "age": patient.get_age(),
                "address": str(patient.address) if patient.address else None,
                "is_insured": patient.is_insured(),
                "insurance": {
                    "code": patient.insurance.code if patient.insurance else None,
                    "discount_rate": patient.insurance.discount_rate if patient.insurance else 0,
                    "valid_until": patient.insurance.valid_until.isoformat() if patient.insurance else None,
                } if patient.insurance else None,
                "created_at": patient.created_at.isoformat(),
                "updated_at": patient.updated_at.isoformat(),
            }
        except Exception as e:
            raise Exception(f"Error fetching patient: {str(e)}")


class GetPatientByAccountIdQueryHandler:
    """Handle: GetPatientByAccountIdQuery"""
    
    def __init__(self, patient_repo: IPatientRepository):
        self.patient_repo = patient_repo
    
    def handle(self, query: GetPatientByAccountIdQuery) -> dict:
        """Get patient by account ID"""
        try:
            patient = self.patient_repo.get_by_account_id(query.account_id)
            
            if not patient:
                return None
            
            # Return same DTO as GetPatientByIdQueryHandler
            handler = GetPatientByIdQueryHandler(self.patient_repo)
            return handler.handle(GetPatientByIdQuery(patient_id=str(patient._id)))
        except Exception as e:
            raise Exception(f"Error fetching patient: {str(e)}")


class GetPatientByEmailQueryHandler:
    """Handle: GetPatientByEmailQuery"""
    
    def __init__(self, patient_repo: IPatientRepository):
        self.patient_repo = patient_repo
    
    def handle(self, query: GetPatientByEmailQuery) -> list:
        """Get patients by email"""
        try:
            patients = self.patient_repo.list_by_email(query.email)
            
            handler = GetPatientByIdQueryHandler(self.patient_repo)
            return [
                handler.handle(GetPatientByIdQuery(patient_id=str(p._id)))
                for p in patients
            ]
        except Exception as e:
            raise Exception(f"Error fetching patients: {str(e)}")


class ListAllPatientsQueryHandler:
    """Handle: ListAllPatientsQuery"""
    
    def __init__(self, patient_repo: IPatientRepository):
        self.patient_repo = patient_repo
    
    def handle(self, query: ListAllPatientsQuery) -> dict:
        """List all patients with pagination"""
        try:
            all_patients = self.patient_repo.list_all()
            
            # Simple pagination
            start = (query.page - 1) * query.page_size
            end = start + query.page_size
            paginated = all_patients[start:end]
            
            handler = GetPatientByIdQueryHandler(self.patient_repo)
            patients_dto = [
                handler.handle(GetPatientByIdQuery(patient_id=str(p._id)))
                for p in paginated
            ]
            
            return {
                "patients": patients_dto,
                "page": query.page,
                "page_size": query.page_size,
                "total": len(all_patients),
                "total_pages": (len(all_patients) + query.page_size - 1) // query.page_size,
            }
        except Exception as e:
            raise Exception(f"Error fetching patients: {str(e)}")


class ListInsuredPatientsQueryHandler:
    """Handle: ListInsuredPatientsQuery"""
    
    def __init__(self, patient_repo: IPatientRepository):
        self.patient_repo = patient_repo
    
    def handle(self, query: ListInsuredPatientsQuery) -> dict:
        """List patients with valid insurance"""
        try:
            insured_patients = self.patient_repo.list_insured_patients()
            
            # Pagination
            start = (query.page - 1) * query.page_size
            end = start + query.page_size
            paginated = insured_patients[start:end]
            
            handler = GetPatientByIdQueryHandler(self.patient_repo)
            patients_dto = [
                handler.handle(GetPatientByIdQuery(patient_id=str(p._id)))
                for p in paginated
            ]
            
            return {
                "patients": patients_dto,
                "page": query.page,
                "page_size": query.page_size,
                "total": len(insured_patients),
                "total_pages": (len(insured_patients) + query.page_size - 1) // query.page_size,
            }
        except Exception as e:
            raise Exception(f"Error fetching insured patients: {str(e)}")


class GetPatientMedicalRecordsQueryHandler:
    """Handle: GetPatientMedicalRecordsQuery"""
    
    def __init__(self, patient_repo: IPatientRepository):
        self.patient_repo = patient_repo
    
    def handle(self, query: GetPatientMedicalRecordsQuery) -> list:
        """Get patient's medical records"""
        try:
            patient = self.patient_repo.get_by_id(PatientId(query.patient_id))
            
            if not patient:
                return []
            
            return [
                {
                    "id": record.id,
                    "visit_date": record.visit_date.isoformat(),
                    "diagnosis": record.diagnosis,
                    "notes": record.notes,
                }
                for record in patient.medical_records
            ]
        except Exception as e:
            raise Exception(f"Error fetching medical records: {str(e)}")
