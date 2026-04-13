"""
Prescription Service Domain Layer - Domain Services
Business logic spanning multiple aggregates or complex operations
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from datetime import datetime, date
from typing import List
from uuid import uuid4

from shared_ddd.base import DomainService
from .value_objects import (
    PrescriptionId, CustomerId, ProductId, CartItem, PrescriberInfo,
    DrugRequirement, Diagnosis, PrescriptionValidity, PrescriptionStatus, Money
)
from .entities import Prescription
from .repositories import IPrescriptionRepository


class PrescriptionCreationService(DomainService):
    """Domain Service: Create prescriptions with validation"""
    
    def __init__(self, prescription_repo: IPrescriptionRepository):
        self.prescription_repo = prescription_repo
    
    def create_prescription(self, customer_id: str, prescriber_info_dict: dict,
                           diagnoses_list: List[dict], validity_dict: dict) -> Prescription:
        """
        Create new prescription
        
        Args:
            customer_id: Customer ID
            prescriber_info_dict: {name, license_number, specialty, hospital}
            diagnoses_list: [{icd10_code, condition_name, notes}]
            validity_dict: {issued_date, valid_until, max_refills}
            
        Returns:
            New Prescription aggregate
        """
        
        prescription_id = PrescriptionId(str(uuid4()))
        customer = CustomerId(customer_id)
        
        # Create prescriber info
        prescriber = PrescriberInfo(
            name=prescriber_info_dict["name"],
            license_number=prescriber_info_dict["license_number"],
            specialty=prescriber_info_dict.get("specialty", ""),
            hospital=prescriber_info_dict.get("hospital", ""),
        )
        
        # Create diagnoses
        diagnoses = []
        for diag_data in diagnoses_list:
            diagnosis = Diagnosis(
                icd10_code=diag_data["icd10_code"],
                condition_name=diag_data["condition_name"],
                notes=diag_data.get("notes", ""),
            )
            diagnoses.append(diagnosis)
        
        # Create validity
        validity = PrescriptionValidity(
            issued_date=validity_dict["issued_date"],
            valid_until=validity_dict["valid_until"],
            max_refills=validity_dict.get("max_refills", 0),
        )
        
        # Create prescription
        prescription = Prescription(
            prescription_id=prescription_id,
            customer_id=customer,
            prescriber_info=prescriber,
            diagnoses=diagnoses,
            validity=validity,
            line_items=[],
            prescription_status=PrescriptionStatus.DRAFT,
        )
        
        return prescription
    
    def validate_prescription_for_creation(self, prescription: Prescription) -> bool:
        """Validate prescription before persisting"""
        
        if not prescription.validity.is_valid():
            raise ValueError("Prescription not valid at creation time")
        
        if not prescription.diagnoses:
            raise ValueError("Prescription must have at least one diagnosis")
        
        return True


class CartManagementService(DomainService):
    """Domain Service: Manage shopping cart items"""
    
    def __init__(self, prescription_repo: IPrescriptionRepository):
        self.prescription_repo = prescription_repo
    
    def add_to_cart(self, prescription: Prescription, product_id: str, sku: str,
                   product_name: str, quantity: int, unit_price: float,
                   currency: str = "VND", requires_prescription: bool = False,
                   drug_requirement_dict: dict = None) -> None:
        """
        Add item to prescription cart
        
        Args:
            prescription: Prescription to add item to
            product_id: Product ID
            sku: Product SKU
            product_name: Product display name
            quantity: Quantity to add
            unit_price: Unit price
            currency: Currency code
            requires_prescription: If drug requires prescription
            drug_requirement_dict: Optional drug requirement details
        """
        
        cart_item = CartItem(
            product_id=ProductId(product_id),
            sku=sku,
            product_name=product_name,
            quantity=quantity,
            unit="box",
            unit_price=unit_price,
            currency=currency,
            requires_prescription=requires_prescription,
        )
        
        drug_requirement = None
        if drug_requirement_dict:
            drug_requirement = DrugRequirement(
                frequency=drug_requirement_dict["frequency"],
                duration=drug_requirement_dict["duration"],
                dosage=drug_requirement_dict["dosage"],
                instructions=drug_requirement_dict.get("instructions", ""),
                warnings=drug_requirement_dict.get("warnings", ""),
            )
        
        prescription.add_item(cart_item, drug_requirement)
    
    def remove_from_cart(self, prescription: Prescription, product_id: str) -> None:
        """Remove item from cart"""
        prescription.remove_item(ProductId(product_id))
    
    def update_cart_item_quantity(self, prescription: Prescription,
                                 product_id: str, new_quantity: int) -> None:
        """Update item quantity"""
        prescription.update_item_quantity(ProductId(product_id), new_quantity)


class PrescriptionProcessingService(DomainService):
    """Domain Service: Process prescription lifecycle"""
    
    def __init__(self, prescription_repo: IPrescriptionRepository):
        self.prescription_repo = prescription_repo
    
    def submit_prescription(self, prescription: Prescription) -> None:
        """Submit prescription for dispensing"""
        prescription.submit_prescription()
    
    def confirm_prescription(self, prescription: Prescription) -> None:
        """Pharmacy confirms prescription"""
        prescription.confirm_prescription()
    
    def fulfill_prescription_item(self, prescription: Prescription,
                                 product_id: str, quantity: int) -> None:
        """Fulfill item from prescription"""
        prescription.fulfill_item(ProductId(product_id), quantity)
    
    def cancel_prescription(self, prescription: Prescription, reason: str = "") -> None:
        """Cancel prescription"""
        prescription.cancel_prescription(reason)


class PrescriptionValidationService(DomainService):
    """Domain Service: Validate prescriptions"""
    
    def __init__(self, prescription_repo: IPrescriptionRepository):
        self.prescription_repo = prescription_repo
    
    def validate_prescription_validity(self, prescription: Prescription, check_date: date = None) -> bool:
        """Check if prescription is valid"""
        return prescription.check_validity()
    
    def check_expiring_prescriptions(self, days_threshold: int = 7) -> List[Prescription]:
        """Get prescriptions expiring soon"""
        
        all_prescriptions = self.prescription_repo.list_active_prescriptions()
        expiring = []
        
        for px in all_prescriptions:
            if px.validity and px.validity.is_expiring_soon(days_threshold):
                expiring.append(px)
        
        return expiring
    
    def get_validity_warning(self, prescription: Prescription) -> str:
        """Get warning text about prescription validity"""
        
        if not prescription.validity:
            return ""
        
        if not prescription.validity.is_valid():
            return "PRESCRIPTION EXPIRED"
        
        days_left = prescription.validity.days_remaining()
        
        if days_left == 0:
            return "PRESCRIPTION EXPIRES TODAY"
        elif days_left <= 3:
            return f"PRESCRIPTION EXPIRES IN {days_left} DAYS"
        else:
            return f"Prescription valid for {days_left} days"
