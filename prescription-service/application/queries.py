"""
Prescription Service Application Layer - Queries
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


# ============================================================================
# Query DTOs
# ============================================================================

@dataclass
class GetPrescriptionByIdQuery:
    """Get prescription by ID"""
    prescription_id: str


@dataclass
class GetPrescriptionsByCustomerQuery:
    """Get prescriptions for a customer"""
    customer_id: str
    limit: int = 20
    offset: int = 0


@dataclass
class ListPrescriptionsByStatusQuery:
    """List prescriptions with specific status"""
    status: str  # DRAFT, SUBMITTED, CONFIRMED, FULFILLED, CANCELLED, EXPIRED
    limit: int = 20
    offset: int = 0


@dataclass
class ListDraftPrescriptionsQuery:
    """List all draft (not submitted) prescriptions"""
    limit: int = 20
    offset: int = 0


@dataclass
class ListSubmittedPrescriptionsQuery:
    """List all submitted prescriptions (waiting for confirmation)"""
    limit: int = 20
    offset: int = 0


@dataclass
class ListActivePrescriptionsQuery:
    """List active prescriptions (CONFIRMED, not expired)"""
    limit: int = 20
    offset: int = 0


@dataclass
class ListRecentPrescriptionsQuery:
    """List recently created/updated prescriptions"""
    days: int = 7
    limit: int = 20
    offset: int = 0


@dataclass
class SearchPrescriptionQuery:
    """Search prescriptions by customer and status"""
    customer_id: str
    status: Optional[str] = None
    limit: int = 20
    offset: int = 0


@dataclass
class GetPrescriptionItemsQuery:
    """Get line items for a prescription"""
    prescription_id: str


@dataclass
class CheckPrescriptionValidityQuery:
    """Check if prescription is valid"""
    prescription_id: str


# ============================================================================
# Result DTOs
# ============================================================================

@dataclass
class CartItemDTO:
    """Cart item data"""
    product_id: str
    sku: str
    product_name: str
    quantity: int
    unit_price: float
    total_price: float
    currency: str
    requires_prescription: bool


@dataclass
class DrugRequirementDTO:
    """Drug requirement data"""
    frequency: str
    duration: str
    dosage: str
    instructions: str
    warnings: str


@dataclass
class PrescriptionLineItemDTO:
    """Prescription line item data"""
    product_id: str
    cart_item: CartItemDTO
    drug_requirement: DrugRequirementDTO
    fulfill_quantity: int
    remaining_quantity: int
    is_fully_fulfilled: bool


@dataclass
class PrescriberDTO:
    """Prescriber information data"""
    name: str
    license_number: str
    specialty: str
    hospital: str


@dataclass
class DiagnosisDTO:
    """Diagnosis data"""
    icd_code: str
    condition_name: str


@dataclass
class PrescriptionValidityDTO:
    """Prescription validity data"""
    issued_date: datetime
    valid_until: datetime
    max_refills: int
    is_valid: bool
    days_remaining: int
    is_expiring_soon: bool


@dataclass
class PrescriptionDetailDTO:
    """Detailed prescription information"""
    prescription_id: str
    customer_id: str
    prescriber: PrescriberDTO
    diagnoses: List[DiagnosisDTO]
    validity: PrescriptionValidityDTO
    line_items: List[PrescriptionLineItemDTO]
    prescription_status: str  # DRAFT, SUBMITTED, CONFIRMED, FULFILLED, CANCELLED, EXPIRED
    cart_status: str  # ACTIVE, SUBMITTED, COMPLETED, ABANDONED
    subtotal: float
    total_amount: float
    currency: str
    created_at: datetime
    submitted_date: Optional[datetime]
    confirmed_date: Optional[datetime]
    fulfilled_date: Optional[datetime]
    notes: Optional[str]


@dataclass
class PrescriptionSummaryDTO:
    """Summary prescription information (for list views)"""
    prescription_id: str
    customer_id: str
    prescriber_name: str
    prescription_status: str
    cart_status: str
    total_amount: float
    item_count: int
    created_at: datetime
    submitted_date: Optional[datetime]
    valid_until: datetime


@dataclass
class PrescriptionListDTO:
    """List of prescriptions with pagination"""
    items: List[PrescriptionSummaryDTO]
    total_count: int
    limit: int
    offset: int


@dataclass
class PrescriptionCheckDTO:
    """Result of prescription validity check"""
    prescription_id: str
    is_valid: bool
    status: str
    days_remaining: int
    message: str
