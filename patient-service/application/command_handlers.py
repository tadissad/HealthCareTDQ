"""
Patient Application Layer - Command Handlers

Command handlers contain use case/application logic:
- They orchestrate domain services and repositories
- They handle cross-cutting concerns (logging, validation)
- They publish domain events to the event bus
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from .commands import (
    RegisterPatientCommand, UpdatePatientInsuranceCommand,
    UpdatePatientContactCommand, UpdatePatientAddressCommand,
    DeactivatePatientCommand
)
from ..domain import (
    PatientId, PatientRegistrationService, PatientContactUpdateService,
    PatientAddressUpdateService, IPatientRepository
)


class RegisterPatientCommandHandler:
    """Handle: RegisterPatientCommand"""
    
    def __init__(self, patient_repo: IPatientRepository):
        self.patient_repo = patient_repo
        self.registration_service = PatientRegistrationService(patient_repo)
    
    def handle(self, command: RegisterPatientCommand) -> dict:
        """
        Execute the register patient command
        
        Returns:
            Dictionary with patient_id and success bool
        """
        try:
            # Create patient via domain service
            patient = self.registration_service.register_new_patient(
                account_id=command.account_id,
                full_name=command.full_name,
                email=command.email,
                phone=command.phone,
                date_of_birth=command.date_of_birth,
                gender=command.gender,
                blood_type=command.blood_type,
            )
            
            # TODO: Publish domain events to event bus
            # event_bus.publish(patient.get_events())
            # patient.clear_events()
            
            return {
                "success": True,
                "patient_id": str(patient.id),
                "message": "Patient registered successfully",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }


class UpdatePatientInsuranceCommandHandler:
    """Handle: UpdatePatientInsuranceCommand"""
    
    def __init__(self, patient_repo: IPatientRepository):
        self.patient_repo = patient_repo
        self.registration_service = PatientRegistrationService(patient_repo)
    
    def handle(self, command: UpdatePatientInsuranceCommand) -> dict:
        """Execute the update insurance command"""
        try:
            patient_id = PatientId(command.patient_id)
            
            self.registration_service.issue_insurance(
                patient_id=patient_id,
                insurance_code=command.insurance_code,
                discount_rate=command.discount_rate,
                valid_days=command.valid_days,
            )
            
            return {
                "success": True,
                "message": "Insurance updated successfully",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }


class UpdatePatientContactCommandHandler:
    """Handle: UpdatePatientContactCommand"""
    
    def __init__(self, patient_repo: IPatientRepository):
        self.patient_repo = patient_repo
        self.contact_service = PatientContactUpdateService(patient_repo)
    
    def handle(self, command: UpdatePatientContactCommand) -> dict:
        """Execute the update contact command"""
        try:
            patient_id = PatientId(command.patient_id)
            
            self.contact_service.update_contact(
                patient_id=patient_id,
                email=command.email,
                phone=command.phone,
            )
            
            return {
                "success": True,
                "message": "Contact information updated",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }


class UpdatePatientAddressCommandHandler:
    """Handle: UpdatePatientAddressCommand"""
    
    def __init__(self, patient_repo: IPatientRepository):
        self.patient_repo = patient_repo
        self.address_service = PatientAddressUpdateService(patient_repo)
    
    def handle(self, command: UpdatePatientAddressCommand) -> dict:
        """Execute the update address command"""
        try:
            patient_id = PatientId(command.patient_id)
            
            self.address_service.update_address(
                patient_id=patient_id,
                street=command.street,
                ward=command.ward,
                district=command.district,
                province=command.province,
                postal_code=command.postal_code,
            )
            
            return {
                "success": True,
                "message": "Address updated",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }


class DeactivatePatientCommandHandler:
    """Handle: DeactivatePatientCommand"""
    
    def __init__(self, patient_repo: IPatientRepository):
        self.patient_repo = patient_repo
    
    def handle(self, command: DeactivatePatientCommand) -> dict:
        """Execute the deactivate patient command"""
        try:
            patient_id = PatientId(command.patient_id)
            patient = self.patient_repo.get_by_id(patient_id)
            
            if not patient:
                return {
                    "success": False,
                    "error": f"Patient {command.patient_id} not found",
                }
            
            # TODO: Implement deactivation logic
            # For now, just remove the patient
            self.patient_repo.remove(patient)
            
            return {
                "success": True,
                "message": "Patient deactivated",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
