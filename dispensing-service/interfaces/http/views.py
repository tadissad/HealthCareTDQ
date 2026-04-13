"""
Dispensing Service Interface Layer - HTTP Controllers (Django Views)
Order management REST API endpoints
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

import json
from datetime import datetime

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from application import (
    # Commands
    CreateOrderCommand, ConfirmOrderCommand, DispenseOrderItemCommand,
    ProcessPaymentCommand, HandlePaymentFailureCommand, CancelOrderCommand,
    PutOrderOnHoldCommand, ResumeOrderCommand, UpdateShippingAddressCommand,
    RemoveOrderLineItemCommand, ApplyDiscountToOrderCommand, ValidatePrescriptionCommand,
    # Command Handlers
    CreateOrderCommandHandler, ConfirmOrderCommandHandler, DispenseOrderItemCommandHandler,
    ProcessPaymentCommandHandler, HandlePaymentFailureCommandHandler, CancelOrderCommandHandler,
    PutOrderOnHoldCommandHandler, ResumeOrderCommandHandler, UpdateShippingAddressCommandHandler,
    RemoveOrderLineItemCommandHandler, ApplyDiscountToOrderCommandHandler, ValidatePrescriptionCommandHandler,
    # Queries
    GetOrderByIdQuery, GetOrdersByCustomerQuery, ListPendingOrdersQuery,
    ListOrdersReadyForDispensingQuery, ListDispensingOrdersQuery,
    ListOrdersByStatusQuery, ListAllOrdersQuery, SearchOrdersByCustomerAndStatusQuery,
    ListOrdersWithPrescriptionQuery, GetRecentOrdersQuery, GetOrderInventoryQuery, SearchOrdersQuery,
    # Query Handlers
    GetOrderByIdQueryHandler, GetOrdersByCustomerQueryHandler, ListPendingOrdersQueryHandler,
    ListOrdersReadyForDispensingQueryHandler, ListDispensingOrdersQueryHandler,
    ListOrdersByStatusQueryHandler, ListAllOrdersQueryHandler, SearchOrdersByCustomerAndStatusQueryHandler,
    ListOrdersWithPrescriptionQueryHandler, GetRecentOrdersQueryHandler, GetOrderInventoryQueryHandler,
)

from infrastructure import OrderRepositoryImpl


# Initialize repository
order_repo = OrderRepositoryImpl()


def parse_json_body(request):
    """Parse JSON body from request"""
    try:
        return json.loads(request.body)
    except json.JSONDecodeError:
        return None


def error_response(message, status=400):
    """Return error response"""
    return JsonResponse({
        "success": False,
        "error": message,
    }, status=status)


def success_response(data, status=200):
    """Return success response"""
    return JsonResponse({
        "success": True,
        "data": data,
    }, status=status)


# ============================================================================
# COMMAND ENDPOINTS (POST - state-changing operations)
# ============================================================================

@require_http_methods(["POST"])
def create_order(request):
    """POST /api/orders/create - Create new order"""
    body = parse_json_body(request)
    if not body:
        return error_response("Invalid JSON body")
    
    try:
        command = CreateOrderCommand(
            customer_id=body.get("customer_id"),
            line_items=body.get("line_items", []),
            payment_method=body.get("payment_method", "CASH"),
            shipping_address=body.get("shipping_address"),
            prescription_id=body.get("prescription_id"),
            prescription_info=body.get("prescription_info"),
            notes=body.get("notes", ""),
        )
        
        handler = CreateOrderCommandHandler(order_repo)
        result = handler.handle(command)
        
        return success_response(result, status=201)
    
    except Exception as e:
        return error_response(f"Error creating order: {str(e)}", status=400)


@require_http_methods(["POST"])
def confirm_order(request):
    """POST /api/orders/<order_id>/confirm - Confirm order"""
    body = parse_json_body(request)
    
    try:
        order_id = request.POST.get("order_id") or body.get("order_id")
        
        command = ConfirmOrderCommand(
            order_id=order_id,
            payment_authorized=body.get("payment_authorized", False) if body else False,
            transaction_id=body.get("transaction_id") if body else None,
        )
        
        handler = ConfirmOrderCommandHandler(order_repo)
        result = handler.handle(command)
        
        return success_response(result)
    
    except Exception as e:
        return error_response(f"Error confirming order: {str(e)}", status=400)


@require_http_methods(["POST"])
def dispense_order_item(request):
    """POST /api/orders/<order_id>/dispense - Dispense item from order"""
    body = parse_json_body(request)
    if not body:
        return error_response("Invalid JSON body")
    
    try:
        order_id = request.POST.get("order_id") or body.get("order_id")
        
        command = DispenseOrderItemCommand(
            order_id=order_id,
            product_id=body.get("product_id"),
            quantity=int(body.get("quantity", 0)),
            unit=body.get("unit", "box"),
            dispensed_by=body.get("dispensed_by", "SYSTEM"),
        )
        
        handler = DispenseOrderItemCommandHandler(order_repo)
        result = handler.handle(command)
        
        return success_response(result)
    
    except Exception as e:
        return error_response(f"Error dispensing item: {str(e)}", status=400)


@require_http_methods(["POST"])
def process_payment(request):
    """POST /api/orders/<order_id>/payment - Process payment"""
    body = parse_json_body(request)
    if not body:
        return error_response("Invalid JSON body")
    
    try:
        order_id = request.POST.get("order_id") or body.get("order_id")
        
        command = ProcessPaymentCommand(
            order_id=order_id,
            payment_method=body.get("payment_method", "CASH"),
            amount=float(body.get("amount", 0)),
            transaction_id=body.get("transaction_id"),
            reference_number=body.get("reference_number"),
        )
        
        handler = ProcessPaymentCommandHandler(order_repo)
        result = handler.handle(command)
        
        return success_response(result)
    
    except Exception as e:
        return error_response(f"Error processing payment: {str(e)}", status=400)


@require_http_methods(["POST"])
def handle_payment_failure(request):
    """POST /api/orders/<order_id>/payment-failure - Record payment failure"""
    body = parse_json_body(request)
    if not body:
        return error_response("Invalid JSON body")
    
    try:
        order_id = request.POST.get("order_id") or body.get("order_id")
        
        command = HandlePaymentFailureCommand(
            order_id=order_id,
            failure_reason=body.get("failure_reason", "Unknown"),
            attempted_amount=float(body.get("attempted_amount", 0)),
            payment_method=body.get("payment_method", "UNKNOWN"),
        )
        
        handler = HandlePaymentFailureCommandHandler(order_repo)
        result = handler.handle(command)
        
        return success_response(result)
    
    except Exception as e:
        return error_response(f"Error handling payment failure: {str(e)}", status=400)


@require_http_methods(["POST"])
def cancel_order(request):
    """POST /api/orders/<order_id>/cancel - Cancel order"""
    body = parse_json_body(request)
    if not body:
        return error_response("Invalid JSON body")
    
    try:
        order_id = request.POST.get("order_id") or body.get("order_id")
        
        command = CancelOrderCommand(
            order_id=order_id,
            cancellation_reason=body.get("cancellation_reason", "Customer request"),
        )
        
        handler = CancelOrderCommandHandler(order_repo)
        result = handler.handle(command)
        
        return success_response(result)
    
    except Exception as e:
        return error_response(f"Error cancelling order: {str(e)}", status=400)


@require_http_methods(["POST"])
def put_order_on_hold(request):
    """POST /api/orders/<order_id>/hold - Put order on hold"""
    body = parse_json_body(request)
    if not body:
        return error_response("Invalid JSON body")
    
    try:
        order_id = request.POST.get("order_id") or body.get("order_id")
        
        command = PutOrderOnHoldCommand(
            order_id=order_id,
            hold_reason=body.get("hold_reason", "Unknown"),
        )
        
        handler = PutOrderOnHoldCommandHandler(order_repo)
        result = handler.handle(command)
        
        return success_response(result)
    
    except Exception as e:
        return error_response(f"Error putting order on hold: {str(e)}", status=400)


@require_http_methods(["POST"])
def resume_order(request):
    """POST /api/orders/<order_id>/resume - Resume order from hold"""
    body = parse_json_body(request)
    if not body:
        return error_response("Invalid JSON body")
    
    try:
        order_id = request.POST.get("order_id") or body.get("order_id")
        
        command = ResumeOrderCommand(order_id=order_id)
        
        handler = ResumeOrderCommandHandler(order_repo)
        result = handler.handle(command)
        
        return success_response(result)
    
    except Exception as e:
        return error_response(f"Error resuming order: {str(e)}", status=400)


@require_http_methods(["POST"])
def update_shipping_address(request):
    """POST /api/orders/<order_id>/shipping - Update shipping address"""
    body = parse_json_body(request)
    if not body:
        return error_response("Invalid JSON body")
    
    try:
        order_id = request.POST.get("order_id") or body.get("order_id")
        
        command = UpdateShippingAddressCommand(
            order_id=order_id,
            street=body.get("street"),
            city=body.get("city"),
            district=body.get("district"),
            postal_code=body.get("postal_code"),
            country=body.get("country", "Vietnam"),
            notes=body.get("notes", ""),
        )
        
        handler = UpdateShippingAddressCommandHandler(order_repo)
        result = handler.handle(command)
        
        return success_response(result)
    
    except Exception as e:
        return error_response(f"Error updating address: {str(e)}", status=400)


@require_http_methods(["POST"])
def remove_line_item(request):
    """POST /api/orders/<order_id>/remove-item - Remove item from order"""
    body = parse_json_body(request)
    if not body:
        return error_response("Invalid JSON body")
    
    try:
        order_id = request.POST.get("order_id") or body.get("order_id")
        
        command = RemoveOrderLineItemCommand(
            order_id=order_id,
            product_id=body.get("product_id"),
        )
        
        handler = RemoveOrderLineItemCommandHandler(order_repo)
        result = handler.handle(command)
        
        return success_response(result)
    
    except Exception as e:
        return error_response(f"Error removing item: {str(e)}", status=400)


@require_http_methods(["POST"])
def apply_discount(request):
    """POST /api/orders/<order_id>/discount - Apply discount to order"""
    body = parse_json_body(request)
    if not body:
        return error_response("Invalid JSON body")
    
    try:
        order_id = request.POST.get("order_id") or body.get("order_id")
        
        command = ApplyDiscountToOrderCommand(
            order_id=order_id,
            discount_percent=float(body.get("discount_percent", 0)),
            reason=body.get("reason", "Customer discount"),
        )
        
        handler = ApplyDiscountToOrderCommandHandler(order_repo)
        result = handler.handle(command)
        
        return success_response(result)
    
    except Exception as e:
        return error_response(f"Error applying discount: {str(e)}", status=400)


@require_http_methods(["POST"])
def validate_prescription(request):
    """POST /api/orders/<order_id>/validate-prescription - Validate prescription"""
    body = parse_json_body(request)
    if not body:
        return error_response("Invalid JSON body")
    
    try:
        order_id = request.POST.get("order_id") or body.get("order_id")
        
        command = ValidatePrescriptionCommand(order_id=order_id)
        
        handler = ValidatePrescriptionCommandHandler(order_repo)
        result = handler.handle(command)
        
        return success_response(result)
    
    except Exception as e:
        return error_response(f"Error validating prescription: {str(e)}", status=400)


# ============================================================================
# QUERY ENDPOINTS (GET - read operations)
# ============================================================================

@require_http_methods(["GET"])
def get_order_by_id(request, order_id):
    """GET /api/orders/<order_id> - Get order by ID"""
    try:
        query = GetOrderByIdQuery(order_id=order_id)
        handler = GetOrderByIdQueryHandler(order_repo)
        result = handler.handle(query)
        
        if not result:
            return error_response("Order not found", status=404)
        
        return success_response(result)
    
    except Exception as e:
        return error_response(f"Error fetching order: {str(e)}", status=400)


@require_http_methods(["GET"])
def get_customer_orders(request, customer_id):
    """GET /api/customers/<customer_id>/orders - Get customer's orders"""
    try:
        page = int(request.GET.get("page", 1))
        page_size = int(request.GET.get("page_size", 20))
        
        query = GetOrdersByCustomerQuery(
            customer_id=customer_id,
            page=page,
            page_size=page_size
        )
        handler = GetOrdersByCustomerQueryHandler(order_repo)
        result = handler.handle(query)
        
        return success_response(result)
    
    except Exception as e:
        return error_response(f"Error fetching orders: {str(e)}", status=400)


@require_http_methods(["GET"])
def list_pending_orders(request):
    """GET /api/orders/pending - List pending orders"""
    try:
        page = int(request.GET.get("page", 1))
        page_size = int(request.GET.get("page_size", 20))
        
        query = ListPendingOrdersQuery(page=page, page_size=page_size)
        handler = ListPendingOrdersQueryHandler(order_repo)
        result = handler.handle(query)
        
        return success_response(result)
    
    except Exception as e:
        return error_response(f"Error fetching orders: {str(e)}", status=400)


@require_http_methods(["GET"])
def list_ready_for_dispensing(request):
    """GET /api/orders/ready-for-dispensing - List confirmed orders ready to dispense"""
    try:
        page = int(request.GET.get("page", 1))
        page_size = int(request.GET.get("page_size", 20))
        
        query = ListOrdersReadyForDispensingQuery(page=page, page_size=page_size)
        handler = ListOrdersReadyForDispensingQueryHandler(order_repo)
        result = handler.handle(query)
        
        return success_response(result)
    
    except Exception as e:
        return error_response(f"Error fetching orders: {str(e)}", status=400)


@require_http_methods(["GET"])
def list_dispensing_orders(request):
    """GET /api/orders/dispensing - List orders being dispensed"""
    try:
        page = int(request.GET.get("page", 1))
        page_size = int(request.GET.get("page_size", 20))
        
        query = ListDispensingOrdersQuery(page=page, page_size=page_size)
        handler = ListDispensingOrdersQueryHandler(order_repo)
        result = handler.handle(query)
        
        return success_response(result)
    
    except Exception as e:
        return error_response(f"Error fetching orders: {str(e)}", status=400)


@require_http_methods(["GET"])
def list_orders_by_status(request, status):
    """GET /api/orders/status/<status> - List orders by status"""
    try:
        page = int(request.GET.get("page", 1))
        page_size = int(request.GET.get("page_size", 20))
        
        query = ListOrdersByStatusQuery(
            status=status,
            page=page,
            page_size=page_size
        )
        handler = ListOrdersByStatusQueryHandler(order_repo)
        result = handler.handle(query)
        
        return success_response(result)
    
    except Exception as e:
        return error_response(f"Error fetching orders: {str(e)}", status=400)


@require_http_methods(["GET"])
def list_all_orders(request):
    """GET /api/orders - List all orders"""
    try:
        page = int(request.GET.get("page", 1))
        page_size = int(request.GET.get("page_size", 20))
        
        query = ListAllOrdersQuery(page=page, page_size=page_size)
        handler = ListAllOrdersQueryHandler(order_repo)
        result = handler.handle(query)
        
        return success_response(result)
    
    except Exception as e:
        return error_response(f"Error fetching orders: {str(e)}", status=400)


@require_http_methods(["GET"])
def list_prescription_orders(request):
    """GET /api/orders/with-prescription - List orders with prescription"""
    try:
        page = int(request.GET.get("page", 1))
        page_size = int(request.GET.get("page_size", 20))
        
        query = ListOrdersWithPrescriptionQuery(page=page, page_size=page_size)
        handler = ListOrdersWithPrescriptionQueryHandler(order_repo)
        result = handler.handle(query)
        
        return success_response(result)
    
    except Exception as e:
        return error_response(f"Error fetching orders: {str(e)}", status=400)


@require_http_methods(["GET"])
def get_recent_orders(request):
    """GET /api/orders/recent - Get most recent orders"""
    try:
        limit = int(request.GET.get("limit", 10))
        
        query = GetRecentOrdersQuery(limit=limit)
        handler = GetRecentOrdersQueryHandler(order_repo)
        result = handler.handle(query)
        
        return success_response(result)
    
    except Exception as e:
        return error_response(f"Error fetching orders: {str(e)}", status=400)


@require_http_methods(["GET"])
def get_order_inventory(request, order_id):
    """GET /api/orders/<order_id>/inventory - Get order inventory details"""
    try:
        query = GetOrderInventoryQuery(order_id=order_id)
        handler = GetOrderInventoryQueryHandler(order_repo)
        result = handler.handle(query)
        
        if not result:
            return error_response("Order not found", status=404)
        
        return success_response(result)
    
    except Exception as e:
        return error_response(f"Error fetching inventory: {str(e)}", status=400)


@require_http_methods(["GET"])
def health_check(request):
    """GET /api/orders/health - Health check"""
    return success_response({"status": "healthy", "service": "dispensing"})
