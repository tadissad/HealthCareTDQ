"""
Dispensing Service Application Layer - Command Handlers
Orchestrates domain services based on commands, returns DTOs
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from datetime import datetime

from .commands import (
    CreateOrderCommand, ConfirmOrderCommand, DispenseOrderItemCommand,
    ProcessPaymentCommand, HandlePaymentFailureCommand, CancelOrderCommand,
    PutOrderOnHoldCommand, ResumeOrderCommand, UpdateShippingAddressCommand,
    RemoveOrderLineItemCommand, ApplyDiscountToOrderCommand, ValidatePrescriptionCommand
)
from ..domain import (
    Order, IOrderRepository, OrderCreationService, OrderProcessingService,
    OrderPaymentService, PrescriptionValidationService,
    CustomerId, ProductId, ShippingAddress
)


class CreateOrderCommandHandler:
    """Handle: CreateOrderCommand"""
    
    def __init__(self, order_repo: IOrderRepository):
        self.order_repo = order_repo
        self.creation_service = OrderCreationService(order_repo)
    
    def handle(self, command: CreateOrderCommand) -> dict:
        try:
            # Create order using domain service
            order = self.creation_service.create_order(
                customer_id=command.customer_id,
                line_items=command.line_items,
                payment_method=command.payment_method,
                shipping_address_dict=command.shipping_address,
                prescription_info_dict=command.prescription_info,
            )
            
            # Validate before saving
            self.creation_service.validate_order_for_creation(order)
            
            # Persist
            self.order_repo.add(order)
            
            return {
                "success": True,
                "order_id": str(order.order_id),
                "total_amount": order.total_amount.amount,
                "currency": order.total_amount.currency,
                "status": order.status.value if hasattr(order.status, 'value') else str(order.status),
                "line_items_count": len(order.order_items),
                "message": "Order created successfully",
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}


class ConfirmOrderCommandHandler:
    """Handle: ConfirmOrderCommand"""
    
    def __init__(self, order_repo: IOrderRepository):
        self.order_repo = order_repo
        self.processing_service = OrderProcessingService(order_repo)
    
    def handle(self, command: ConfirmOrderCommand) -> dict:
        try:
            # Fetch order
            from ..domain import OrderId
            order = self.order_repo.get_by_id(OrderId(command.order_id))
            
            if not order:
                return {"success": False, "error": "Order not found"}
            
            # Confirm using domain service
            self.processing_service.confirm_order(
                order,
                payment_confirmed=command.payment_authorized
            )
            
            # Persist changes
            self.order_repo.update(order)
            
            return {
                "success": True,
                "order_id": str(order.order_id),
                "status": order.status.value if hasattr(order.status, 'value') else str(order.status),
                "message": "Order confirmed successfully",
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}


class DispenseOrderItemCommandHandler:
    """Handle: DispenseOrderItemCommand"""
    
    def __init__(self, order_repo: IOrderRepository):
        self.order_repo = order_repo
        self.processing_service = OrderProcessingService(order_repo)
    
    def handle(self, command: DispenseOrderItemCommand) -> dict:
        try:
            # Fetch order
            from ..domain import OrderId
            order = self.order_repo.get_by_id(OrderId(command.order_id))
            
            if not order:
                return {"success": False, "error": "Order not found"}
            
            # Dispense using domain service
            self.processing_service.dispense_order_item(
                order,
                product_id=command.product_id,
                quantity=command.quantity,
                dispensed_by=command.dispensed_by
            )
            
            # Persist changes
            self.order_repo.update(order)
            
            return {
                "success": True,
                "order_id": str(order.order_id),
                "product_id": command.product_id,
                "quantity_dispensed": command.quantity,
                "status": order.status.value if hasattr(order.status, 'value') else str(order.status),
                "message": "Item dispensed successfully",
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}


class ProcessPaymentCommandHandler:
    """Handle: ProcessPaymentCommand"""
    
    def __init__(self, order_repo: IOrderRepository):
        self.order_repo = order_repo
        self.payment_service = OrderPaymentService(order_repo)
    
    def handle(self, command: ProcessPaymentCommand) -> dict:
        try:
            # Fetch order
            from ..domain import OrderId
            order = self.order_repo.get_by_id(OrderId(command.order_id))
            
            if not order:
                return {"success": False, "error": "Order not found"}
            
            # Process payment using domain service
            self.payment_service.process_payment(
                order,
                transaction_id=command.transaction_id,
                reference_number=command.reference_number or ""
            )
            
            # Persist changes
            self.order_repo.update(order)
            
            return {
                "success": True,
                "order_id": str(order.order_id),
                "amount_paid": command.amount,
                "transaction_id": command.transaction_id,
                "message": "Payment processed successfully",
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}


class HandlePaymentFailureCommandHandler:
    """Handle: HandlePaymentFailureCommand"""
    
    def __init__(self, order_repo: IOrderRepository):
        self.order_repo = order_repo
        self.payment_service = OrderPaymentService(order_repo)
    
    def handle(self, command: HandlePaymentFailureCommand) -> dict:
        try:
            # Fetch order
            from ..domain import OrderId
            order = self.order_repo.get_by_id(OrderId(command.order_id))
            
            if not order:
                return {"success": False, "error": "Order not found"}
            
            # Handle failure using domain service
            self.payment_service.handle_payment_failure(
                order,
                reason=command.failure_reason
            )
            
            # Persist changes
            self.order_repo.update(order)
            
            return {
                "success": True,
                "order_id": str(order.order_id),
                "failure_reason": command.failure_reason,
                "message": "Payment failure recorded",
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}


class CancelOrderCommandHandler:
    """Handle: CancelOrderCommand"""
    
    def __init__(self, order_repo: IOrderRepository):
        self.order_repo = order_repo
        self.processing_service = OrderProcessingService(order_repo)
    
    def handle(self, command: CancelOrderCommand) -> dict:
        try:
            # Fetch order
            from ..domain import OrderId
            order = self.order_repo.get_by_id(OrderId(command.order_id))
            
            if not order:
                return {"success": False, "error": "Order not found"}
            
            # Cancel using domain service
            self.processing_service.cancel_order(order, command.cancellation_reason)
            
            # Persist changes
            self.order_repo.update(order)
            
            return {
                "success": True,
                "order_id": str(order.order_id),
                "status": "CANCELLED",
                "cancellation_reason": command.cancellation_reason,
                "message": "Order cancelled successfully",
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}


class PutOrderOnHoldCommandHandler:
    """Handle: PutOrderOnHoldCommand"""
    
    def __init__(self, order_repo: IOrderRepository):
        self.order_repo = order_repo
        self.processing_service = OrderProcessingService(order_repo)
    
    def handle(self, command: PutOrderOnHoldCommand) -> dict:
        try:
            # Fetch order
            from ..domain import OrderId
            order = self.order_repo.get_by_id(OrderId(command.order_id))
            
            if not order:
                return {"success": False, "error": "Order not found"}
            
            # Put on hold using domain service
            self.processing_service.put_order_on_hold(order, command.hold_reason)
            
            # Persist changes
            self.order_repo.update(order)
            
            return {
                "success": True,
                "order_id": str(order.order_id),
                "status": "ON_HOLD",
                "hold_reason": command.hold_reason,
                "message": "Order placed on hold",
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}


class ResumeOrderCommandHandler:
    """Handle: ResumeOrderCommand"""
    
    def __init__(self, order_repo: IOrderRepository):
        self.order_repo = order_repo
        self.processing_service = OrderProcessingService(order_repo)
    
    def handle(self, command: ResumeOrderCommand) -> dict:
        try:
            # Fetch order
            from ..domain import OrderId
            order = self.order_repo.get_by_id(OrderId(command.order_id))
            
            if not order:
                return {"success": False, "error": "Order not found"}
            
            # Resume using domain service
            self.processing_service.resume_order(order)
            
            # Persist changes
            self.order_repo.update(order)
            
            return {
                "success": True,
                "order_id": str(order.order_id),
                "status": order.status.value if hasattr(order.status, 'value') else str(order.status),
                "message": "Order resumed successfully",
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}


class UpdateShippingAddressCommandHandler:
    """Handle: UpdateShippingAddressCommand"""
    
    def __init__(self, order_repo: IOrderRepository):
        self.order_repo = order_repo
    
    def handle(self, command: UpdateShippingAddressCommand) -> dict:
        try:
            # Fetch order
            from ..domain import OrderId
            order = self.order_repo.get_by_id(OrderId(command.order_id))
            
            if not order:
                return {"success": False, "error": "Order not found"}
            
            # Update shipping address
            new_address = ShippingAddress(
                street=command.street,
                city=command.city,
                district=command.district,
                postal_code=command.postal_code,
                country=command.country or "Vietnam",
                notes=command.notes or ""
            )
            
            order.update_shipping_address(new_address)
            
            # Persist changes
            self.order_repo.update(order)
            
            return {
                "success": True,
                "order_id": str(order.order_id),
                "new_address": new_address.format_address(),
                "message": "Shipping address updated successfully",
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}


class RemoveOrderLineItemCommandHandler:
    """Handle: RemoveOrderLineItemCommand"""
    
    def __init__(self, order_repo: IOrderRepository):
        self.order_repo = order_repo
    
    def handle(self, command: RemoveOrderLineItemCommand) -> dict:
        try:
            # Fetch order
            from ..domain import OrderId
            order = self.order_repo.get_by_id(OrderId(command.order_id))
            
            if not order:
                return {"success": False, "error": "Order not found"}
            
            # Remove line item
            order.remove_line_item(ProductId(command.product_id))
            
            # Persist changes
            self.order_repo.update(order)
            
            return {
                "success": True,
                "order_id": str(order.order_id),
                "removed_product_id": command.product_id,
                "new_total": order.total_amount.amount,
                "message": "Line item removed successfully",
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}


class ApplyDiscountToOrderCommandHandler:
    """Handle: ApplyDiscountToOrderCommand"""
    
    def __init__(self, order_repo: IOrderRepository):
        self.order_repo = order_repo
        self.payment_service = OrderPaymentService(order_repo)
    
    def handle(self, command: ApplyDiscountToOrderCommand) -> dict:
        try:
            # Fetch order
            from ..domain import OrderId
            order = self.order_repo.get_by_id(OrderId(command.order_id))
            
            if not order:
                return {"success": False, "error": "Order not found"}
            
            # Calculate discounted total
            from ..domain import Money
            discounted_total = self.payment_service.calculate_total_with_discount(
                order,
                command.discount_percent
            )
            
            # Update discount amount
            discount_amount = order.total_amount.subtract(discounted_total)
            order.discount_amount = discount_amount
            
            # Persist changes
            self.order_repo.update(order)
            
            return {
                "success": True,
                "order_id": str(order.order_id),
                "discount_percent": command.discount_percent,
                "discount_amount": discount_amount.amount,
                "new_total": discounted_total.amount,
                "message": f"Discount of {command.discount_percent}% applied",
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}


class ValidatePrescriptionCommandHandler:
    """Handle: ValidatePrescriptionCommand"""
    
    def __init__(self, order_repo: IOrderRepository):
        self.order_repo = order_repo
        self.prescription_service = PrescriptionValidationService(order_repo)
    
    def handle(self, command: ValidatePrescriptionCommand) -> dict:
        try:
            # Fetch order
            from ..domain import OrderId
            order = self.order_repo.get_by_id(OrderId(command.order_id))
            
            if not order:
                return {"success": False, "error": "Order not found"}
            
            # Validate prescription
            is_valid = self.prescription_service.validate_prescription(order)
            
            warning = self.prescription_service.get_prescription_expiry_warning(order)
            
            return {
                "success": True if is_valid else False,
                "order_id": str(order.order_id),
                "prescription_valid": is_valid,
                "warning": warning,
                "message": "Prescription validation completed",
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "prescription_valid": False,
            }
