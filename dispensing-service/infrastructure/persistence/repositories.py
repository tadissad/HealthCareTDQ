"""
Dispensing Service Infrastructure Layer - Repository Implementation
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from datetime import datetime, date
from typing import List, Optional
from uuid import uuid4

from .models import OrderModel, OrderItemModel
from ...domain import (
    Order, OrderItem, OrderId, CustomerId, ProductId, Money,
    Quantity, LineItem, ShippingAddress, PaymentInfo, PrescriptionInfo,
    OrderStatus, PaymentStatus, PaymentMethod, IOrderRepository
)


class OrderRepositoryImpl(IOrderRepository):
    """
    Implementation of IOrderRepository using Django ORM
    Handles bidirectional mapping between domain Order aggregate and ORM models
    """
    
    def _model_to_entity(self, model: OrderModel) -> Order:
        """Transform OrderModel ORM to Order domain entity"""
        
        # Load order items
        item_models = OrderItemModel.objects.filter(order=model)
        order_items = []
        
        for item_model in item_models:
            line_item = LineItem(
                product_id=ProductId(item_model.product_id),
                sku=item_model.sku,
                product_name=item_model.product_name,
                quantity=Quantity(
                    value=item_model.quantity_ordered,
                    unit=item_model.quantity_unit
                ),
                unit_price=Money(
                    amount=float(item_model.unit_price),
                    currency=item_model.currency
                ),
                line_total=Money(
                    amount=float(item_model.line_total),
                    currency=item_model.currency
                )
            )
            
            order_item = OrderItem(
                order_item_id=item_model.order_item_id,
                line_item=line_item,
                dispensed_quantity=Quantity(
                    value=item_model.quantity_dispensed,
                    unit=item_model.quantity_unit
                )
            )
            order_items.append(order_item)
        
        # Reconstruct shipping address
        shipping_address = None
        if model.shipping_street:
            shipping_address = ShippingAddress(
                street=model.shipping_street,
                city=model.shipping_city,
                district=model.shipping_district,
                postal_code=model.shipping_postal_code,
                country=model.shipping_country,
                notes=model.shipping_notes
            )
        
        # Reconstruct prescription info
        prescription_info = None
        if model.has_prescription and model.prescription_id:
            prescription_info = PrescriptionInfo(
                prescription_id=model.prescription_id,
                prescriber_name=model.prescriber_name,
                prescription_date=model.prescription_date,
                valid_until=model.prescription_valid_until
            )
        
        # Reconstruct payment info
        payment_info = PaymentInfo(
            method=PaymentMethod[model.payment_method],
            status=PaymentStatus[model.payment_status],
            transaction_id=model.transaction_id or "",
            reference_number=model.reference_number or ""
        )
        
        # Reconstruct order
        order = Order(
            order_id=OrderId(model.order_id),
            customer_id=CustomerId(model.customer_id),
            order_items=order_items,
            status=OrderStatus[model.status],
            payment_info=payment_info,
            prescription_info=prescription_info,
            shipping_address=shipping_address,
            order_date=model.order_date,
            confirmed_date=model.confirmed_date,
            dispensed_date=model.dispensed_date,
            total_amount=Money(
                amount=float(model.total_amount),
                currency=model.currency
            ),
            discount_amount=Money(
                amount=float(model.discount_amount),
                currency=model.currency
            ),
            notes=model.notes
        )
        
        return order
    
    def _entity_to_model(self, order: Order) -> OrderModel:
        """Transform Order domain entity to OrderModel ORM"""
        
        model = OrderModel(
            order_id=str(order.order_id),
            customer_id=str(order.customer_id),
            status=order.status.value,
            total_amount=order.total_amount.amount,
            currency=order.total_amount.currency,
            discount_amount=order.discount_amount.amount if order.discount_amount else 0,
            payment_method=order.payment_info.method.value,
            payment_status=order.payment_info.status.value,
            transaction_id=order.payment_info.transaction_id or "",
            reference_number=order.payment_info.reference_number or "",
            has_prescription=order.prescription_info is not None,
            notes=order.notes,
        )
        
        # Set shipping address fields
        if order.shipping_address:
            model.shipping_street = order.shipping_address.street
            model.shipping_city = order.shipping_address.city
            model.shipping_district = order.shipping_address.district
            model.shipping_postal_code = order.shipping_address.postal_code
            model.shipping_country = order.shipping_address.country
            model.shipping_notes = order.shipping_address.notes
        
        # Set prescription fields
        if order.prescription_info:
            model.prescription_id = order.prescription_info.prescription_id
            model.prescriber_name = order.prescription_info.prescriber_name
            model.prescription_date = order.prescription_info.prescription_date
            model.prescription_valid_until = order.prescription_info.valid_until
        
        # Set audit dates
        if order.order_date:
            model.order_date = order.order_date
        if order.confirmed_date:
            model.confirmed_date = order.confirmed_date
        if order.dispensed_date:
            model.dispensed_date = order.dispensed_date
        
        return model
    
    def add(self, order: Order) -> None:
        """Persist new order to database"""
        
        # Save order model
        model = self._entity_to_model(order)
        model.save()
        
        # Save order items
        for order_item in order.order_items:
            item_model = OrderItemModel(
                order_item_id=order_item.order_item_id or str(uuid4()),
                order_id=str(order.order_id),
                product_id=str(order_item.line_item.product_id),
                sku=order_item.line_item.sku,
                product_name=order_item.line_item.product_name,
                quantity_ordered=order_item.line_item.quantity.value,
                quantity_dispensed=order_item.dispensed_quantity.value,
                quantity_unit=order_item.line_item.quantity.unit,
                unit_price=order_item.line_item.unit_price.amount,
                line_total=order_item.line_item.line_total.amount,
                currency=order_item.line_item.unit_price.currency
            )
            item_model.save()
    
    def update(self, order: Order) -> None:
        """Update existing order in database"""
        
        try:
            model = OrderModel.objects.get(order_id=str(order.order_id))
        except OrderModel.DoesNotExist:
            raise Exception(f"Order {order.order_id} not found")
        
        # Update order model
        updated_model = self._entity_to_model(order)
        model.status = updated_model.status
        model.total_amount = updated_model.total_amount
        model.currency = updated_model.currency
        model.discount_amount = updated_model.discount_amount
        model.payment_method = updated_model.payment_method
        model.payment_status = updated_model.payment_status
        model.transaction_id = updated_model.transaction_id
        model.reference_number = updated_model.reference_number
        model.shipping_street = updated_model.shipping_street
        model.shipping_city = updated_model.shipping_city
        model.shipping_district = updated_model.shipping_district
        model.shipping_postal_code = updated_model.shipping_postal_code
        model.shipping_country = updated_model.shipping_country
        model.shipping_notes = updated_model.shipping_notes
        model.has_prescription = updated_model.has_prescription
        model.prescription_id = updated_model.prescription_id
        model.prescriber_name = updated_model.prescriber_name
        model.prescription_date = updated_model.prescription_date
        model.prescription_valid_until = updated_model.prescription_valid_until
        model.confirmed_date = updated_model.confirmed_date
        model.dispensed_date = updated_model.dispensed_date
        model.notes = updated_model.notes
        model.updated_at = datetime.now()
        model.save()
        
        # Update order items
        OrderItemModel.objects.filter(order_id=str(order.order_id)).delete()
        for order_item in order.order_items:
            item_model = OrderItemModel(
                order_item_id=order_item.order_item_id or str(uuid4()),
                order_id=str(order.order_id),
                product_id=str(order_item.line_item.product_id),
                sku=order_item.line_item.sku,
                product_name=order_item.line_item.product_name,
                quantity_ordered=order_item.line_item.quantity.value,
                quantity_dispensed=order_item.dispensed_quantity.value,
                quantity_unit=order_item.line_item.quantity.unit,
                unit_price=order_item.line_item.unit_price.amount,
                line_total=order_item.line_item.line_total.amount,
                currency=order_item.line_item.unit_price.currency
            )
            item_model.save()
    
    def remove(self, order_id: OrderId) -> None:
        """Delete order from database"""
        try:
            model = OrderModel.objects.get(order_id=str(order_id))
            model.delete()
        except OrderModel.DoesNotExist:
            pass
    
    def get_by_id(self, order_id: OrderId) -> Optional[Order]:
        """Retrieve order by ID"""
        try:
            model = OrderModel.objects.get(order_id=str(order_id))
            return self._model_to_entity(model)
        except OrderModel.DoesNotExist:
            return None
    
    def get_by_customer_id(self, customer_id: CustomerId) -> List[Order]:
        """Retrieve all orders for a customer"""
        models = OrderModel.objects.filter(customer_id=str(customer_id)).order_by('-order_date')
        return [self._model_to_entity(m) for m in models]
    
    def list_by_status(self, status: OrderStatus) -> List[Order]:
        """Retrieve orders by status"""
        models = OrderModel.objects.filter(status=status.value).order_by('-order_date')
        return [self._model_to_entity(m) for m in models]
    
    def list_pending_orders(self) -> List[Order]:
        """Retrieve pending orders"""
        models = OrderModel.objects.filter(status='PENDING').order_by('-order_date')
        return [self._model_to_entity(m) for m in models]
    
    def list_orders_ready_for_dispensing(self) -> List[Order]:
        """Retrieve confirmed orders ready for dispensing"""
        models = OrderModel.objects.filter(status='CONFIRMED').order_by('order_date')
        return [self._model_to_entity(m) for m in models]
    
    def list_dispensing_orders(self) -> List[Order]:
        """Retrieve orders currently being dispensed"""
        models = OrderModel.objects.filter(status='DISPENSING').order_by('order_date')
        return [self._model_to_entity(m) for m in models]
    
    def list_all(self) -> List[Order]:
        """Retrieve all orders"""
        models = OrderModel.objects.all().order_by('-order_date')
        return [self._model_to_entity(m) for m in models]
    
    def search_by_customer_and_status(self, customer_id: CustomerId, status: OrderStatus) -> List[Order]:
        """Retrieve orders by customer and status"""
        models = OrderModel.objects.filter(
            customer_id=str(customer_id),
            status=status.value
        ).order_by('-order_date')
        return [self._model_to_entity(m) for m in models]
    
    def list_orders_with_prescription(self) -> List[Order]:
        """Retrieve orders that include prescription items"""
        models = OrderModel.objects.filter(has_prescription=True).order_by('-order_date')
        return [self._model_to_entity(m) for m in models]
    
    def list_recent_orders(self, limit: int = 10) -> List[Order]:
        """Retrieve most recent orders"""
        models = OrderModel.objects.all().order_by('-order_date')[:limit]
        return [self._model_to_entity(m) for m in models]
