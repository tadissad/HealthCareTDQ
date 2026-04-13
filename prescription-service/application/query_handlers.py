"""
Prescription Service Application Layer - Query Handlers
"""

from typing import List, Optional
from datetime import datetime, timedelta

from prescription_service.domain import (
    IPrescriptionRepository, PrescriptionId, PrescriptionStatus
)
from .queries import (
    GetPrescriptionByIdQuery, GetPrescriptionsByCustomerQuery,
    ListPrescriptionsByStatusQuery, ListDraftPrescriptionsQuery,
    ListSubmittedPrescriptionsQuery, ListActivePrescriptionsQuery,
    ListRecentPrescriptionsQuery, SearchPrescriptionQuery,
    GetPrescriptionItemsQuery, CheckPrescriptionValidityQuery,
    CartItemDTO, DrugRequirementDTO, PrescriptionLineItemDTO,
    PrescriberDTO, DiagnosisDTO, PrescriptionValidityDTO,
    PrescriptionDetailDTO, PrescriptionSummaryDTO, PrescriptionListDTO,
    PrescriptionCheckDTO
)


def _map_to_detail_dto(prescription) -> PrescriptionDetailDTO:
    """Map prescription entity to detailed DTO"""
    # Map prescriber
    prescriber_dto = PrescriberDTO(
        name=prescription.prescriber_info.prescriber_name,
        license_number=prescription.prescriber_info.license_number,
        specialty=prescription.prescriber_info.specialty,
        hospital=prescription.prescriber_info.hospital
    )
    
    # Map diagnoses
    diagnoses_dto = [
        DiagnosisDTO(
            icd_code=diag.icd_code,
            condition_name=diag.condition_name
        )
        for diag in prescription.diagnoses
    ]
    
    # Map validity
    validity_dto = PrescriptionValidityDTO(
        issued_date=prescription.validity.issued_date,
        valid_until=prescription.validity.valid_until,
        max_refills=prescription.validity.max_refills,
        is_valid=prescription.validity.is_valid(),
        days_remaining=prescription.validity.days_remaining(),
        is_expiring_soon=prescription.validity.is_expiring_soon()
    )
    
    # Map line items
    line_items_dto = []
    for line_item in prescription.line_items:
        cart_item_dto = CartItemDTO(
            product_id=line_item.cart_item.product_id.value,
            sku=line_item.cart_item.sku,
            product_name=line_item.cart_item.product_name,
            quantity=line_item.cart_item.quantity,
            unit_price=line_item.cart_item.unit_price,
            total_price=line_item.cart_item.unit_price * line_item.cart_item.quantity,
            currency=line_item.cart_item.currency,
            requires_prescription=line_item.cart_item.requires_prescription
        )
        
        drug_req_dto = DrugRequirementDTO(
            frequency=line_item.drug_requirement.frequency,
            duration=line_item.drug_requirement.duration,
            dosage=line_item.drug_requirement.dosage,
            instructions=line_item.drug_requirement.instructions,
            warnings=line_item.drug_requirement.warnings
        )
        
        line_item_dto = PrescriptionLineItemDTO(
            product_id=line_item.cart_item.product_id.value,
            cart_item=cart_item_dto,
            drug_requirement=drug_req_dto,
            fulfill_quantity=line_item.fulfill_quantity,
            remaining_quantity=line_item.remaining_quantity(),
            is_fully_fulfilled=line_item.is_fully_fulfilled()
        )
        line_items_dto.append(line_item_dto)
    
    return PrescriptionDetailDTO(
        prescription_id=prescription.prescription_id.value,
        customer_id=prescription.customer_id.value,
        prescriber=prescriber_dto,
        diagnoses=diagnoses_dto,
        validity=validity_dto,
        line_items=line_items_dto,
        prescription_status=prescription.prescription_status.value,
        cart_status=prescription.cart_status.value,
        subtotal=prescription.subtotal.amount,
        total_amount=prescription.total_amount.amount,
        currency=prescription.total_amount.currency,
        created_at=prescription.created_at,
        submitted_date=prescription.submitted_date,
        confirmed_date=prescription.confirmed_date,
        fulfilled_date=prescription.fulfilled_date,
        notes=prescription.notes
    )


def _map_to_summary_dto(prescription) -> PrescriptionSummaryDTO:
    """Map prescription entity to summary DTO"""
    return PrescriptionSummaryDTO(
        prescription_id=prescription.prescription_id.value,
        customer_id=prescription.customer_id.value,
        prescriber_name=prescription.prescriber_info.prescriber_name,
        prescription_status=prescription.prescription_status.value,
        cart_status=prescription.cart_status.value,
        total_amount=prescription.total_amount.amount,
        item_count=len(prescription.line_items),
        created_at=prescription.created_at,
        submitted_date=prescription.submitted_date,
        valid_until=prescription.validity.valid_until
    )


class GetPrescriptionByIdHandler:
    """Get prescription by ID"""
    
    def __init__(self, repository: IPrescriptionRepository):
        self.repository = repository
    
    def handle(self, query: GetPrescriptionByIdQuery) -> Optional[PrescriptionDetailDTO]:
        """Get prescription details by ID"""
        prescription = self.repository.get_by_id(PrescriptionId(query.prescription_id))
        if not prescription:
            return None
        return _map_to_detail_dto(prescription)


class GetPrescriptionsByCustomerHandler:
    """Get prescriptions for a customer"""
    
    def __init__(self, repository: IPrescriptionRepository):
        self.repository = repository
    
    def handle(self, query: GetPrescriptionsByCustomerQuery) -> PrescriptionListDTO:
        """Get prescriptions for specific customer with pagination"""
        prescriptions = self.repository.get_by_customer_id(query.customer_id)
        
        # Apply pagination
        total_count = len(prescriptions)
        items = prescriptions[query.offset:query.offset + query.limit]
        
        # Map to DTOs
        summary_dtos = [_map_to_summary_dto(p) for p in items]
        
        return PrescriptionListDTO(
            items=summary_dtos,
            total_count=total_count,
            limit=query.limit,
            offset=query.offset
        )


class ListPrescriptionsByStatusHandler:
    """List prescriptions by status"""
    
    def __init__(self, repository: IPrescriptionRepository):
        self.repository = repository
    
    def handle(self, query: ListPrescriptionsByStatusQuery) -> PrescriptionListDTO:
        """List prescriptions with specific status"""
        prescriptions = self.repository.list_by_status(query.status)
        
        # Apply pagination
        total_count = len(prescriptions)
        items = prescriptions[query.offset:query.offset + query.limit]
        
        # Map to DTOs
        summary_dtos = [_map_to_summary_dto(p) for p in items]
        
        return PrescriptionListDTO(
            items=summary_dtos,
            total_count=total_count,
            limit=query.limit,
            offset=query.offset
        )


class ListDraftPrescriptionsHandler:
    """List draft prescriptions"""
    
    def __init__(self, repository: IPrescriptionRepository):
        self.repository = repository
    
    def handle(self, query: ListDraftPrescriptionsQuery) -> PrescriptionListDTO:
        """List all draft (DRAFT status) prescriptions"""
        prescriptions = self.repository.list_draft_prescriptions()
        
        # Apply pagination
        total_count = len(prescriptions)
        items = prescriptions[query.offset:query.offset + query.limit]
        
        # Map to DTOs
        summary_dtos = [_map_to_summary_dto(p) for p in items]
        
        return PrescriptionListDTO(
            items=summary_dtos,
            total_count=total_count,
            limit=query.limit,
            offset=query.offset
        )


class ListSubmittedPrescriptionsHandler:
    """List submitted prescriptions"""
    
    def __init__(self, repository: IPrescriptionRepository):
        self.repository = repository
    
    def handle(self, query: ListSubmittedPrescriptionsQuery) -> PrescriptionListDTO:
        """List all submitted (SUBMITTED status) prescriptions"""
        prescriptions = self.repository.list_submitted_prescriptions()
        
        # Apply pagination
        total_count = len(prescriptions)
        items = prescriptions[query.offset:query.offset + query.limit]
        
        # Map to DTOs
        summary_dtos = [_map_to_summary_dto(p) for p in items]
        
        return PrescriptionListDTO(
            items=summary_dtos,
            total_count=total_count,
            limit=query.limit,
            offset=query.offset
        )


class ListActivePrescriptionsHandler:
    """List active prescriptions"""
    
    def __init__(self, repository: IPrescriptionRepository):
        self.repository = repository
    
    def handle(self, query: ListActivePrescriptionsQuery) -> PrescriptionListDTO:
        """List active (CONFIRMED, not expired) prescriptions"""
        prescriptions = self.repository.list_active_prescriptions()
        
        # Apply pagination
        total_count = len(prescriptions)
        items = prescriptions[query.offset:query.offset + query.limit]
        
        # Map to DTOs
        summary_dtos = [_map_to_summary_dto(p) for p in items]
        
        return PrescriptionListDTO(
            items=summary_dtos,
            total_count=total_count,
            limit=query.limit,
            offset=query.offset
        )


class ListRecentPrescriptionsHandler:
    """List recent prescriptions"""
    
    def __init__(self, repository: IPrescriptionRepository):
        self.repository = repository
    
    def handle(self, query: ListRecentPrescriptionsQuery) -> PrescriptionListDTO:
        """List prescriptions created/updated recently"""
        cutoff_date = datetime.now() - timedelta(days=query.days)
        all_prescriptions = self.repository.list_all()
        
        # Filter by recent date
        recent = [
            p for p in all_prescriptions
            if p.created_at >= cutoff_date or (p.submitted_date and p.submitted_date >= cutoff_date)
        ]
        
        # Apply pagination
        total_count = len(recent)
        items = recent[query.offset:query.offset + query.limit]
        
        # Map to DTOs
        summary_dtos = [_map_to_summary_dto(p) for p in items]
        
        return PrescriptionListDTO(
            items=summary_dtos,
            total_count=total_count,
            limit=query.limit,
            offset=query.offset
        )


class SearchPrescriptionHandler:
    """Search prescriptions"""
    
    def __init__(self, repository: IPrescriptionRepository):
        self.repository = repository
    
    def handle(self, query: SearchPrescriptionQuery) -> PrescriptionListDTO:
        """Search prescriptions by customer and optional status"""
        prescriptions = self.repository.search_by_customer_and_status(
            query.customer_id, query.status
        )
        
        # Apply pagination
        total_count = len(prescriptions)
        items = prescriptions[query.offset:query.offset + query.limit]
        
        # Map to DTOs
        summary_dtos = [_map_to_summary_dto(p) for p in items]
        
        return PrescriptionListDTO(
            items=summary_dtos,
            total_count=total_count,
            limit=query.limit,
            offset=query.offset
        )


class GetPrescriptionItemsHandler:
    """Get line items for a prescription"""
    
    def __init__(self, repository: IPrescriptionRepository):
        self.repository = repository
    
    def handle(self, query: GetPrescriptionItemsQuery) -> List[PrescriptionLineItemDTO]:
        """Get all line items for a prescription"""
        prescription = self.repository.get_by_id(PrescriptionId(query.prescription_id))
        if not prescription:
            return []
        
        line_items_dto = []
        for line_item in prescription.line_items:
            cart_item_dto = CartItemDTO(
                product_id=line_item.cart_item.product_id.value,
                sku=line_item.cart_item.sku,
                product_name=line_item.cart_item.product_name,
                quantity=line_item.cart_item.quantity,
                unit_price=line_item.cart_item.unit_price,
                total_price=line_item.cart_item.unit_price * line_item.cart_item.quantity,
                currency=line_item.cart_item.currency,
                requires_prescription=line_item.cart_item.requires_prescription
            )
            
            drug_req_dto = DrugRequirementDTO(
                frequency=line_item.drug_requirement.frequency,
                duration=line_item.drug_requirement.duration,
                dosage=line_item.drug_requirement.dosage,
                instructions=line_item.drug_requirement.instructions,
                warnings=line_item.drug_requirement.warnings
            )
            
            line_item_dto = PrescriptionLineItemDTO(
                product_id=line_item.cart_item.product_id.value,
                cart_item=cart_item_dto,
                drug_requirement=drug_req_dto,
                fulfill_quantity=line_item.fulfill_quantity,
                remaining_quantity=line_item.remaining_quantity(),
                is_fully_fulfilled=line_item.is_fully_fulfilled()
            )
            line_items_dto.append(line_item_dto)
        
        return line_items_dto


class CheckPrescriptionValidityHandler:
    """Check prescription validity"""
    
    def __init__(self, repository: IPrescriptionRepository):
        self.repository = repository
    
    def handle(self, query: CheckPrescriptionValidityQuery) -> PrescriptionCheckDTO:
        """Check if prescription is valid"""
        prescription = self.repository.get_by_id(PrescriptionId(query.prescription_id))
        if not prescription:
            return PrescriptionCheckDTO(
                prescription_id=query.prescription_id,
                is_valid=False,
                status="NOT_FOUND",
                days_remaining=0,
                message="Prescription not found"
            )
        
        is_valid = prescription.check_validity()
        days_remaining = prescription.validity.days_remaining()
        
        if not is_valid:
            if prescription.prescription_status == PrescriptionStatus.EXPIRED:
                message = "Prescription has expired"
            else:
                message = "Prescription is not valid"
        elif prescription.validity.is_expiring_soon():
            message = f"Prescription is valid but expiring soon ({days_remaining} days remaining)"
        else:
            message = f"Prescription is valid ({days_remaining} days remaining)"
        
        return PrescriptionCheckDTO(
            prescription_id=query.prescription_id,
            is_valid=is_valid,
            status=prescription.prescription_status.value,
            days_remaining=days_remaining,
            message=message
        )
