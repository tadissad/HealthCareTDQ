"""
Prescription Service Application Layer - Command Handlers
"""

from typing import Optional
from datetime import datetime, timedelta
from uuid import uuid4

from shared_ddd.base import DomainService
from prescription_service.domain import (
    Prescription, PrescriptionId, CustomerId, ProductId, PrescriberInfo,
    CartItem, DrugRequirement, Diagnosis, PrescriptionValidity, Money,
    PrescriptionCreationService, CartManagementService,
    PrescriptionProcessingService, PrescriptionValidationService,
    IPrescriptionRepository
)
from .commands import (
    CreatePrescriptionCommand, AddCartItemCommand, RemoveCartItemCommand,
    UpdateCartItemQuantityCommand, SubmitPrescriptionCommand,
    ConfirmPrescriptionCommand, FulfillPrescriptionItemCommand,
    CancelPrescriptionCommand, ClearCartCommand,
    CreatePrescriptionResult, CartOperationResult,
    PrescriptionStatusChangeResult, FulfillmentResult
)


class CreatePrescriptionHandler:
    """Handle prescription creation"""
    
    def __init__(self, repository: IPrescriptionRepository):
        self.repository = repository
        self.creation_service = PrescriptionCreationService()
    
    def handle(self, command: CreatePrescriptionCommand) -> CreatePrescriptionResult:
        """Create a new prescription"""
        prescription_id = PrescriptionId(str(uuid4()))
        customer_id = CustomerId(command.customer_id)
        
        # Create prescriber info VO
        prescriber_info = PrescriberInfo(
            prescriber_name=command.prescriber_name,
            license_number=command.prescriber_license_number,
            specialty=command.prescriber_specialty,
            hospital=command.prescriber_hospital
        )
        
        # Create diagnoses VOs
        diagnoses = [
            Diagnosis(
                icd_code=diag["icd_code"],
                condition_name=diag["condition_name"]
            )
            for diag in command.diagnoses
        ]
        
        # Create validity VO
        issued_date = datetime.now()
        valid_until = issued_date + timedelta(days=command.validity_days)
        validity = PrescriptionValidity(
            issued_date=issued_date,
            valid_until=valid_until,
            max_refills=command.max_refills
        )
        
        # Use domain service to create prescription
        prescription = self.creation_service.create_prescription(
            prescription_id=prescription_id,
            customer=customer_id,
            prescriber=prescriber_info,
            diagnoses=diagnoses,
            validity=validity
        )
        
        # Persist the new prescription
        self.repository.add(prescription)
        
        # Return result
        return CreatePrescriptionResult(
            prescription_id=prescription_id.value,
            customer_id=customer_id.value,
            status="DRAFT",
            created_at=datetime.now()
        )


class AddCartItemHandler:
    """Handle adding item to prescription cart"""
    
    def __init__(self, repository: IPrescriptionRepository):
        self.repository = repository
        self.cart_service = CartManagementService()
    
    def handle(self, command: AddCartItemCommand) -> CartOperationResult:
        """Add item to cart"""
        prescription = self.repository.get_by_id(PrescriptionId(command.prescription_id))
        if not prescription:
            raise ValueError(f"Prescription {command.prescription_id} not found")
        
        # Create cart item VO
        cart_item = CartItem(
            product_id=ProductId(command.product_id),
            sku=command.sku,
            product_name=command.product_name,
            quantity=command.quantity,
            unit_price=command.unit_price,
            currency=command.currency,
            requires_prescription=command.requires_prescription
        )
        
        # Create drug requirement VO
        drug_requirement = DrugRequirement(
            frequency=command.frequency,
            duration=command.duration,
            dosage=command.dosage,
            instructions=command.instructions,
            warnings=command.warnings
        )
        
        # Use domain service and entity method to add to cart
        self.cart_service.add_to_cart(prescription, cart_item, drug_requirement)
        
        # Persist changes
        self.repository.update(prescription)
        
        # Return result
        return CartOperationResult(
            prescription_id=prescription.prescription_id.value,
            total_items=len(prescription.line_items),
            total_amount=prescription.total_amount.amount,
            operation="add"
        )


class RemoveCartItemHandler:
    """Handle removing item from prescription cart"""
    
    def __init__(self, repository: IPrescriptionRepository):
        self.repository = repository
        self.cart_service = CartManagementService()
    
    def handle(self, command: RemoveCartItemCommand) -> CartOperationResult:
        """Remove item from cart"""
        prescription = self.repository.get_by_id(PrescriptionId(command.prescription_id))
        if not prescription:
            raise ValueError(f"Prescription {command.prescription_id} not found")
        
        product_id = ProductId(command.product_id)
        
        # Use domain service and entity method
        self.cart_service.remove_from_cart(prescription, product_id)
        
        # Persist changes
        self.repository.update(prescription)
        
        return CartOperationResult(
            prescription_id=prescription.prescription_id.value,
            total_items=len(prescription.line_items),
            total_amount=prescription.total_amount.amount,
            operation="remove"
        )


class UpdateCartItemQuantityHandler:
    """Handle updating cart item quantity"""
    
    def __init__(self, repository: IPrescriptionRepository):
        self.repository = repository
        self.cart_service = CartManagementService()
    
    def handle(self, command: UpdateCartItemQuantityCommand) -> CartOperationResult:
        """Update cart item quantity"""
        prescription = self.repository.get_by_id(PrescriptionId(command.prescription_id))
        if not prescription:
            raise ValueError(f"Prescription {command.prescription_id} not found")
        
        product_id = ProductId(command.product_id)
        
        # Use domain service
        self.cart_service.update_cart_item_quantity(
            prescription, product_id, command.new_quantity
        )
        
        # Persist changes
        self.repository.update(prescription)
        
        return CartOperationResult(
            prescription_id=prescription.prescription_id.value,
            total_items=len(prescription.line_items),
            total_amount=prescription.total_amount.amount,
            operation="update"
        )


class SubmitPrescriptionHandler:
    """Handle prescription submission"""
    
    def __init__(self, repository: IPrescriptionRepository):
        self.repository = repository
        self.processing_service = PrescriptionProcessingService()
    
    def handle(self, command: SubmitPrescriptionCommand) -> PrescriptionStatusChangeResult:
        """Submit prescription from DRAFT to SUBMITTED"""
        prescription = self.repository.get_by_id(PrescriptionId(command.prescription_id))
        if not prescription:
            raise ValueError(f"Prescription {command.prescription_id} not found")
        
        old_status = prescription.prescription_status.value
        
        # Use domain service to submit
        self.processing_service.submit_prescription(prescription)
        
        # Persist changes
        self.repository.update(prescription)
        
        return PrescriptionStatusChangeResult(
            prescription_id=prescription.prescription_id.value,
            old_status=old_status,
            new_status=prescription.prescription_status.value,
            changed_at=datetime.now()
        )


class ConfirmPrescriptionHandler:
    """Handle prescription confirmation"""
    
    def __init__(self, repository: IPrescriptionRepository):
        self.repository = repository
        self.processing_service = PrescriptionProcessingService()
    
    def handle(self, command: ConfirmPrescriptionCommand) -> PrescriptionStatusChangeResult:
        """Confirm prescription from SUBMITTED to CONFIRMED"""
        prescription = self.repository.get_by_id(PrescriptionId(command.prescription_id))
        if not prescription:
            raise ValueError(f"Prescription {command.prescription_id} not found")
        
        old_status = prescription.prescription_status.value
        
        # Use domain service to confirm
        self.processing_service.confirm_prescription(prescription)
        
        # Persist changes
        self.repository.update(prescription)
        
        return PrescriptionStatusChangeResult(
            prescription_id=prescription.prescription_id.value,
            old_status=old_status,
            new_status=prescription.prescription_status.value,
            changed_at=datetime.now()
        )


class FulfillPrescriptionItemHandler:
    """Handle prescription item fulfillment"""
    
    def __init__(self, repository: IPrescriptionRepository):
        self.repository = repository
        self.processing_service = PrescriptionProcessingService()
    
    def handle(self, command: FulfillPrescriptionItemCommand) -> FulfillmentResult:
        """Fulfill (dispense) a prescription line item"""
        prescription = self.repository.get_by_id(PrescriptionId(command.prescription_id))
        if not prescription:
            raise ValueError(f"Prescription {command.prescription_id} not found")
        
        product_id = ProductId(command.product_id)
        
        # Get line item before fulfillment
        line_item = None
        for li in prescription.line_items:
            if li.cart_item.product_id.value == product_id.value:
                line_item = li
                break
        
        if not line_item:
            raise ValueError(f"Product {command.product_id} not found in prescription")
        
        # Use domain service to fulfill
        self.processing_service.fulfill_prescription_item(
            prescription, product_id, command.fulfill_quantity
        )
        
        # Persist changes
        self.repository.update(prescription)
        
        # Get updated line item
        for li in prescription.line_items:
            if li.cart_item.product_id.value == product_id.value:
                line_item = li
                break
        
        return FulfillmentResult(
            prescription_id=prescription.prescription_id.value,
            product_id=product_id.value,
            fulfilled_quantity=command.fulfill_quantity,
            remaining_quantity=line_item.remaining_quantity() if line_item else 0,
            fully_fulfilled=line_item.is_fully_fulfilled() if line_item else False
        )


class CancelPrescriptionHandler:
    """Handle prescription cancellation"""
    
    def __init__(self, repository: IPrescriptionRepository):
        self.repository = repository
        self.processing_service = PrescriptionProcessingService()
    
    def handle(self, command: CancelPrescriptionCommand) -> PrescriptionStatusChangeResult:
        """Cancel entire prescription"""
        prescription = self.repository.get_by_id(PrescriptionId(command.prescription_id))
        if not prescription:
            raise ValueError(f"Prescription {command.prescription_id} not found")
        
        old_status = prescription.prescription_status.value
        
        # Use domain service to cancel
        self.processing_service.cancel_prescription(prescription, command.reason)
        
        # Persist changes
        self.repository.update(prescription)
        
        return PrescriptionStatusChangeResult(
            prescription_id=prescription.prescription_id.value,
            old_status=old_status,
            new_status=prescription.prescription_status.value,
            changed_at=datetime.now()
        )


class ClearCartHandler:
    """Handle clearing all items from cart"""
    
    def __init__(self, repository: IPrescriptionRepository):
        self.repository = repository
    
    def handle(self, command: ClearCartCommand) -> CartOperationResult:
        """Clear all cart items"""
        prescription = self.repository.get_by_id(PrescriptionId(command.prescription_id))
        if not prescription:
            raise ValueError(f"Prescription {command.prescription_id} not found")
        
        # Clear cart via entity method
        prescription.clear_cart()
        
        # Persist changes
        self.repository.update(prescription)
        
        return CartOperationResult(
            prescription_id=prescription.prescription_id.value,
            total_items=len(prescription.line_items),
            total_amount=prescription.total_amount.amount,
            operation="clear"
        )
