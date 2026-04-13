"""
Dispensing Service Domain Layer - Domain Services
Business logic for order management that spans multiple aggregates
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from datetime import datetime, date
from typing import List
from uuid import uuid4

from shared_ddd.base import DomainService
from .value_objects import (
    OrderId, CustomerId, ProductId, Money, Quantity, LineItem,
    ShippingAddress, PaymentInfo, PrescriptionInfo, PaymentMethod, PaymentStatus
)
from .entities import Order, OrderItem
from .repositories import IOrderRepository


class OrderCreationService(DomainService):
    """
    Domain Service: Create orders with validation
    Handles complex order creation logic and initialization
    """
    
    def __init__(self, order_repo: IOrderRepository):
        self.order_repo = order_repo
    
    def create_order(self, customer_id: str, line_items: List[dict],
                     payment_method: str, shipping_address_dict: dict = None,
                     prescription_info_dict: dict = None) -> Order:
        """
        Create new order with line items
        
        Args:
            customer_id: Customer placing order
            line_items: List of {product_id, sku, name, quantity, unit_price, currency}
            payment_method: Payment method (CASH, CARD, INSURANCE, etc)
            shipping_address_dict: Shipping address details
            prescription_info_dict: Prescription info if needed
            
        Returns:
            New Order aggregate
        """
        
        order_id = OrderId(str(uuid4()))
        customer = CustomerId(customer_id)
        
        # Create line items
        items = []
        total = Money(0, "VND")
        
        for item_data in line_items:
            product_id = ProductId(item_data["product_id"])
            quantity = Quantity(
                value=item_data["quantity"],
                unit=item_data.get("unit", "box")
            )
            
            unit_price = Money(
                amount=float(item_data["unit_price"]),
                currency=item_data.get("currency", "VND")
            )
            
            line_total = unit_price.multiply(quantity.value)
            
            line_item = LineItem(
                product_id=product_id,
                sku=item_data["sku"],
                product_name=item_data["name"],
                quantity=quantity,
                unit_price=unit_price,
                line_total=line_total
            )
            
            items.append(line_item)
            if total.currency != unit_price.currency:
                total = Money(total.amount, unit_price.currency)
            total = total.add(line_total)
        
        # Create shipping address
        shipping_address = None
        if shipping_address_dict:
            shipping_address = ShippingAddress(
                street=shipping_address_dict["street"],
                city=shipping_address_dict["city"],
                district=shipping_address_dict["district"],
                postal_code=shipping_address_dict["postal_code"],
                country=shipping_address_dict.get("country", "Vietnam"),
                notes=shipping_address_dict.get("notes", "")
            )
        
        # Create prescription info if needed
        prescription_info = None
        if prescription_info_dict:
            prescription_info = PrescriptionInfo(
                prescription_id=prescription_info_dict["prescription_id"],
                prescriber_name=prescription_info_dict["prescriber_name"],
                prescription_date=prescription_info_dict["prescription_date"],
                valid_until=prescription_info_dict["valid_until"]
            )
        
        # Create payment info
        payment_info = PaymentInfo(
            method=PaymentMethod[payment_method.upper()],
            status=PaymentStatus.PENDING
        )
        
        # Create order
        order = Order(
            order_id=order_id,
            customer_id=customer,
            order_items=[],
            status="PENDING",
            payment_info=payment_info,
            prescription_info=prescription_info,
            shipping_address=shipping_address,
            total_amount=total,
        )
        
        # Add line items
        for line_item in items:
            order.add_line_item(line_item)
        
        return order
    
    def validate_order_for_creation(self, order: Order) -> bool:
        """Validate order before persisting"""
        
        if not order.order_items:
            raise ValueError("Order must have at least one line item")
        
        if order.total_amount.amount <= 0:
            raise ValueError("Order total must be greater than zero")
        
        if order.payment_info.status not in [PaymentStatus.PENDING, PaymentStatus.AUTHORIZED]:
            raise ValueError("Invalid payment status for new order")
        
        return True


class OrderProcessingService(DomainService):
    """
    Domain Service: Process order lifecycle
    Manages transitions between order states
    """
    
    def __init__(self, order_repo: IOrderRepository):
        self.order_repo = order_repo
    
    def confirm_order(self, order: Order, payment_confirmed: bool = False) -> None:
        """
        Confirm order ready for dispensing
        
        Args:
            order: Order to confirm
            payment_confirmed: Whether payment has been confirmed
        """
        
        if payment_confirmed:
            order.mark_payment_processed(
                transaction_id=str(uuid4()),
                reference_number=f"REF-{datetime.now().timestamp()}"
            )
        
        order.confirm_order()
    
    def dispense_order_item(self, order: Order, product_id: str,
                            quantity: int, dispensed_by: str) -> None:
        """
        Dispense item from order
        
        Args:
            order: Order containing item
            product_id: Product to dispense
            quantity: Quantity to dispense
            dispensed_by: Staff member dispensing
        """
        
        order.dispense_item(
            ProductId(product_id),
            Quantity(value=quantity, unit="box"),
            dispensed_by
        )
    
    def cancel_order(self, order: Order, reason: str = "") -> None:
        """Cancel order"""
        order.cancel_order(reason)
    
    def put_order_on_hold(self, order: Order, reason: str) -> None:
        """Temporarily suspend order"""
        order.put_on_hold(reason)
    
    def resume_order(self, order: Order) -> None:
        """Resume order from hold"""
        order.resume_from_hold()


class OrderPaymentService(DomainService):
    """
    Domain Service: Handle payment operations
    Orchestrates payment processing and validation
    """
    
    def __init__(self, order_repo: IOrderRepository):
        self.order_repo = order_repo
    
    def process_payment(self, order: Order, transaction_id: str,
                        reference_number: str = "") -> None:
        """
        Record successful payment
        
        Args:
            order: Order for which payment is processed
            transaction_id: Transaction ID from payment gateway
            reference_number: Optional payment reference
        """
        
        order.mark_payment_processed(transaction_id, reference_number)
    
    def handle_payment_failure(self, order: Order, reason: str) -> None:
        """
        Record payment failure
        
        Args:
            order: Order for which payment failed
            reason: Reason for failure
        """
        
        order.mark_payment_failed(reason)
    
    def calculate_total_with_discount(self, order: Order, discount_percent: float) -> Money:
        """
        Calculate order total with discount applied
        
        Args:
            order: Order to calculate total for
            discount_percent: Discount percentage (0-100)
            
        Returns:
            Money object with discounted total
        """
        
        if discount_percent < 0 or discount_percent > 100:
            raise ValueError("Discount percent must be between 0 and 100")
        
        subtotal = order.get_subtotal()
        discount = subtotal.multiply(discount_percent / 100)
        
        return subtotal.subtract(discount)


class PrescriptionValidationService(DomainService):
    """
    Domain Service: Validate prescription for orders
    Checks prescription validity and authorization
    """
    
    def __init__(self, order_repo: IOrderRepository):
        self.order_repo = order_repo
    
    def validate_prescription(self, order: Order, check_date: date = None) -> bool:
        """
        Validate prescription on order
        
        Args:
            order: Order with prescription to validate
            check_date: Date to validate against (default today)
            
        Returns:
            True if prescription is valid
            
        Raises:
            ValueError if prescription invalid
        """
        
        if not order.prescription_info:
            return True  # No prescription required
        
        if not order.prescription_info.is_valid(check_date):
            raise ValueError("Prescription is expired or not yet valid")
        
        return True
    
    def get_prescription_expiry_warning(self, order: Order) -> str:
        """Get warning about prescription expiring soon"""
        
        if not order.prescription_info:
            return ""
        
        days_left = order.prescription_info.days_until_expiry()
        
        if days_left < 0:
            return "PRESCRIPTION EXPIRED"
        elif days_left == 0:
            return "PRESCRIPTION EXPIRES TODAY"
        elif days_left <= 3:
            return f"PRESCRIPTION EXPIRES IN {days_left} DAYS"
        else:
            return f"Prescription valid for {days_left} days"
