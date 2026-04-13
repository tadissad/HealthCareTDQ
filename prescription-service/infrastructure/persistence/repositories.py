"""
Prescription Service Infrastructure Layer - Repository Implementation
"""

import json
from datetime import datetime
from typing import List, Optional

from prescription_service.domain import (
    Prescription, PrescriptionLineItem, PrescriptionId, CustomerId,
    ProductId, PrescriberInfo, CartItem, DrugRequirement, Diagnosis,
    PrescriptionValidity, Money, IPrescriptionRepository, PrescriptionStatus,
    CartStatus
)
from .models import PrescriptionModel, PrescriptionLineItemModel, DomainEventModel


class PrescriptionRepositoryImpl(IPrescriptionRepository):
    """Implementation of prescription repository using Django ORM"""
    
    def add(self, prescription: Prescription) -> None:
        """Add new prescription to repository"""
        # Create prescription model
        pres_model = PrescriptionModel(
            prescription_id=prescription.prescription_id.value,
            customer_id=prescription.customer_id.value,
            prescriber_name=prescription.prescriber_info.prescriber_name,
            prescriber_license_number=prescription.prescriber_info.license_number,
            prescriber_specialty=prescription.prescriber_info.specialty,
            prescriber_hospital=prescription.prescriber_info.hospital,
            diagnoses_json=json.dumps([
                {
                    "icd_code": diag.icd_code,
                    "condition_name": diag.condition_name
                }
                for diag in prescription.diagnoses
            ]),
            valid_until=prescription.validity.valid_until,
            max_refills=prescription.validity.max_refills,
            prescription_status=prescription.prescription_status.value,
            cart_status=prescription.cart_status.value,
            subtotal_amount=prescription.subtotal.amount,
            total_amount=prescription.total_amount.amount,
            currency=prescription.total_amount.currency,
            created_at=prescription.created_at,
            submitted_date=prescription.submitted_date,
            confirmed_date=prescription.confirmed_date,
            fulfilled_date=prescription.fulfilled_date,
            notes=prescription.notes
        )
        pres_model.save()
        
        # Create line items
        for line_item in prescription.line_items:
            self._create_line_item(pres_model, line_item)
        
        # Store domain events
        self._store_events(prescription)
    
    def update(self, prescription: Prescription) -> None:
        """Update existing prescription"""
        pres_model = PrescriptionModel.objects.get(
            prescription_id=prescription.prescription_id.value
        )
        
        # Update prescription fields
        pres_model.prescription_status = prescription.prescription_status.value
        pres_model.cart_status = prescription.cart_status.value
        pres_model.subtotal_amount = prescription.subtotal.amount
        pres_model.total_amount = prescription.total_amount.amount
        pres_model.submitted_date = prescription.submitted_date
        pres_model.confirmed_date = prescription.confirmed_date
        pres_model.fulfilled_date = prescription.fulfilled_date
        pres_model.notes = prescription.notes
        pres_model.save()
        
        # Clear and recreate line items
        pres_model.line_items.all().delete()
        for line_item in prescription.line_items:
            self._create_line_item(pres_model, line_item)
        
        # Store domain events
        self._store_events(prescription)
    
    def remove(self, prescription_id: PrescriptionId) -> None:
        """Remove prescription from repository"""
        PrescriptionModel.objects.filter(
            prescription_id=prescription_id.value
        ).delete()
    
    def get_by_id(self, prescription_id: PrescriptionId) -> Optional[Prescription]:
        """Get prescription by ID"""
        try:
            model = PrescriptionModel.objects.get(
                prescription_id=prescription_id.value
            )
            return self._map_model_to_entity(model)
        except PrescriptionModel.DoesNotExist:
            return None
    
    def get_by_customer_id(self, customer_id: str) -> List[Prescription]:
        """Get all prescriptions for a customer"""
        models = PrescriptionModel.objects.filter(
            customer_id=customer_id
        ).order_by('-created_at')
        return [self._map_model_to_entity(m) for m in models]
    
    def list_by_status(self, status: str) -> List[Prescription]:
        """List prescriptions by status"""
        models = PrescriptionModel.objects.filter(
            prescription_status=status
        ).order_by('-created_at')
        return [self._map_model_to_entity(m) for m in models]
    
    def list_draft_prescriptions(self) -> List[Prescription]:
        """List all draft prescriptions"""
        models = PrescriptionModel.objects.filter(
            prescription_status='DRAFT'
        ).order_by('-created_at')
        return [self._map_model_to_entity(m) for m in models]
    
    def list_submitted_prescriptions(self) -> List[Prescription]:
        """List all submitted prescriptions"""
        models = PrescriptionModel.objects.filter(
            prescription_status='SUBMITTED'
        ).order_by('-submitted_date')
        return [self._map_model_to_entity(m) for m in models]
    
    def list_active_prescriptions(self) -> List[Prescription]:
        """List active (CONFIRMED, not expired) prescriptions"""
        now = datetime.now()
        models = PrescriptionModel.objects.filter(
            prescription_status='CONFIRMED',
            valid_until__gt=now
        ).order_by('-confirmed_date')
        return [self._map_model_to_entity(m) for m in models]
    
    def list_all(self) -> List[Prescription]:
        """List all prescriptions"""
        models = PrescriptionModel.objects.all().order_by('-created_at')
        return [self._map_model_to_entity(m) for m in models]
    
    def search_by_customer_and_status(
        self, customer_id: str, status: Optional[str] = None
    ) -> List[Prescription]:
        """Search prescriptions by customer and optional status"""
        query = PrescriptionModel.objects.filter(customer_id=customer_id)
        if status:
            query = query.filter(prescription_status=status)
        models = query.order_by('-created_at')
        return [self._map_model_to_entity(m) for m in models]
    
    def list_recent(self, days: int = 7) -> List[Prescription]:
        """List recently created prescriptions"""
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(days=days)
        models = PrescriptionModel.objects.filter(
            created_at__gte=cutoff
        ).order_by('-created_at')
        return [self._map_model_to_entity(m) for m in models]
    
    # ========================================================================
    # Private Helper Methods
    # ========================================================================
    
    def _map_model_to_entity(self, model: PrescriptionModel) -> Prescription:
        """Map ORM model to domain entity"""
        # Create value objects
        prescription_id = PrescriptionId(model.prescription_id)
        customer_id = CustomerId(model.customer_id)
        
        prescriber_info = PrescriberInfo(
            prescriber_name=model.prescriber_name,
            license_number=model.prescriber_license_number,
            specialty=model.prescriber_specialty,
            hospital=model.prescriber_hospital
        )
        
        # Parse diagnoses
        diagnoses_data = json.loads(model.diagnoses_json)
        diagnoses = [
            Diagnosis(icd_code=d["icd_code"], condition_name=d["condition_name"])
            for d in diagnoses_data
        ]
        
        # Create validity VO
        validity = PrescriptionValidity(
            issued_date=model.issued_date,
            valid_until=model.valid_until,
            max_refills=model.max_refills
        )
        
        # Map line items
        line_items = []
        for item_model in model.line_items.all():
            line_item = self._map_line_item_model_to_entity(item_model)
            line_items.append(line_item)
        
        # Create money VO
        total_amount = Money(
            amount=float(model.total_amount),
            currency=model.currency
        )
        subtotal = Money(
            amount=float(model.subtotal_amount),
            currency=model.currency
        )
        
        # Create prescription entity
        prescription = Prescription(
            prescription_id=prescription_id,
            customer_id=customer_id,
            prescriber_info=prescriber_info,
            diagnoses=diagnoses,
            validity=validity,
            line_items=line_items,
            prescription_status=PrescriptionStatus[model.prescription_status],
            cart_status=CartStatus[model.cart_status],
            subtotal=subtotal,
            total_amount=total_amount,
            created_at=model.created_at,
            submitted_date=model.submitted_date,
            confirmed_date=model.confirmed_date,
            fulfilled_date=model.fulfilled_date,
            notes=model.notes
        )
        
        return prescription
    
    def _map_line_item_model_to_entity(
        self, model: PrescriptionLineItemModel
    ) -> PrescriptionLineItem:
        """Map line item ORM model to domain entity"""
        cart_item = CartItem(
            product_id=ProductId(model.product_id),
            sku=model.sku,
            product_name=model.product_name,
            quantity=model.quantity,
            unit_price=model.unit_price,
            currency=model.currency,
            requires_prescription=model.requires_prescription
        )
        
        drug_requirement = DrugRequirement(
            frequency=model.frequency,
            duration=model.duration,
            dosage=model.dosage,
            instructions=model.instructions,
            warnings=model.warnings
        )
        
        line_item = PrescriptionLineItem(
            cart_item=cart_item,
            drug_requirement=drug_requirement
        )
        line_item.fulfill_quantity = model.fulfill_quantity
        
        return line_item
    
    def _create_line_item(
        self, pres_model: PrescriptionModel, line_item: PrescriptionLineItem
    ) -> None:
        """Create line item model from entity"""
        PrescriptionLineItemModel.objects.create(
            prescription=pres_model,
            product_id=line_item.cart_item.product_id.value,
            sku=line_item.cart_item.sku,
            product_name=line_item.cart_item.product_name,
            quantity=line_item.cart_item.quantity,
            unit_price=line_item.cart_item.unit_price,
            currency=line_item.cart_item.currency,
            requires_prescription=line_item.cart_item.requires_prescription,
            frequency=line_item.drug_requirement.frequency,
            duration=line_item.drug_requirement.duration,
            dosage=line_item.drug_requirement.dosage,
            instructions=line_item.drug_requirement.instructions,
            warnings=line_item.drug_requirement.warnings,
            fulfill_quantity=line_item.fulfill_quantity
        )
    
    def _store_events(self, prescription: Prescription) -> None:
        """Store domain events"""
        for event in prescription.get_events():
            try:
                DomainEventModel.objects.create(
                    event_id=str(event.event_id),
                    event_type=event.__class__.__name__,
                    aggregate_id=prescription.prescription_id.value,
                    aggregate_type='Prescription',
                    event_data=json.dumps(event.__dict__),
                    occurred_at=event.occurred_at
                )
            except Exception as e:
                # Log but don't fail on event storage
                print(f"Failed to store event: {e}")
