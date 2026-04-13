"""
Prescription Service Application Layer - Commands
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime, timedelta


# ============================================================================
# Command DTOs for Prescription Operations
# ============================================================================

@dataclass
class CreatePrescriptionCommand:
    """Create a new prescription"""
    customer_id: str
    prescriber_name: str
    prescriber_license_number: str
    prescriber_specialty: str
    prescriber_hospital: str
    diagnoses: List[dict]  # [{"icd_code": "I10", "condition_name": "Hypertension"}]
    validity_days: int = 90
    max_refills: int = 3


@dataclass
class AddCartItemCommand:
    """Add an item to prescription cart"""
    prescription_id: str
    product_id: str
    sku: str
    product_name: str
    quantity: int
    unit_price: float
    currency: str = "VND"
    requires_prescription: bool = True
    # Drug requirement details
    frequency: str = ""  # e.g., "2 times per day"
    duration: str = ""   # e.g., "7 days"
    dosage: str = ""     # e.g., "500mg"
    instructions: str = ""
    warnings: str = ""


@dataclass
class RemoveCartItemCommand:
    """Remove an item from prescription cart"""
    prescription_id: str
    product_id: str


@dataclass
class UpdateCartItemQuantityCommand:
    """Update quantity of a cart item"""
    prescription_id: str
    product_id: str
    new_quantity: int


@dataclass
class SubmitPrescriptionCommand:
    """Submit a prescription from DRAFT to SUBMITTED status"""
    prescription_id: str


@dataclass
class ConfirmPrescriptionCommand:
    """Confirm a prescription from SUBMITTED to CONFIRMED status"""
    prescription_id: str


@dataclass
class FulfillPrescriptionItemCommand:
    """Fulfill (dispense) a specific prescription line item"""
    prescription_id: str
    product_id: str
    fulfill_quantity: int


@dataclass
class CancelPrescriptionCommand:
    """Cancel an entire prescription"""
    prescription_id: str
    reason: Optional[str] = None


@dataclass
class ClearCartCommand:
    """Clear all items from prescription cart"""
    prescription_id: str


# ============================================================================
# Command Result DTOs
# ============================================================================

@dataclass
class CreatePrescriptionResult:
    """Result of prescription creation"""
    prescription_id: str
    customer_id: str
    status: str
    created_at: datetime


@dataclass
class CartOperationResult:
    """Result of cart item operations"""
    prescription_id: str
    total_items: int
    total_amount: float
    operation: str  # "add", "remove", "update", "clear"


@dataclass
class PrescriptionStatusChangeResult:
    """Result of prescription status change"""
    prescription_id: str
    old_status: str
    new_status: str
    changed_at: datetime


@dataclass
class FulfillmentResult:
    """Result of prescription item fulfillment"""
    prescription_id: str
    product_id: str
    fulfilled_quantity: int
    remaining_quantity: int
    fully_fulfilled: bool
