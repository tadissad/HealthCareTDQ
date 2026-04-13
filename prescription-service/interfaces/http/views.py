"""
Prescription Service Interface Layer - HTTP Views
"""

from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import json
from typing import Optional

from prescription_service.domain import PrescriptionStatus
from prescription_service.application import (
    # Commands
    CreatePrescriptionCommand, AddCartItemCommand, RemoveCartItemCommand,
    UpdateCartItemQuantityCommand, SubmitPrescriptionCommand,
    ConfirmPrescriptionCommand, FulfillPrescriptionItemCommand,
    CancelPrescriptionCommand, ClearCartCommand,
    # Command Handlers
    CreatePrescriptionHandler, AddCartItemHandler, RemoveCartItemHandler,
    UpdateCartItemQuantityHandler, SubmitPrescriptionHandler,
    ConfirmPrescriptionHandler, FulfillPrescriptionItemHandler,
    CancelPrescriptionHandler, ClearCartHandler,
    # Queries
    GetPrescriptionByIdQuery, GetPrescriptionsByCustomerQuery,
    ListPrescriptionsByStatusQuery, ListDraftPrescriptionsQuery,
    ListSubmittedPrescriptionsQuery, ListActivePrescriptionsQuery,
    ListRecentPrescriptionsQuery, SearchPrescriptionQuery,
    GetPrescriptionItemsQuery, CheckPrescriptionValidityQuery,
    # Query Handlers
    GetPrescriptionByIdHandler, GetPrescriptionsByCustomerHandler,
    ListPrescriptionsByStatusHandler, ListDraftPrescriptionsHandler,
    ListSubmittedPrescriptionsHandler, ListActivePrescriptionsHandler,
    ListRecentPrescriptionsHandler, SearchPrescriptionHandler,
    GetPrescriptionItemsHandler, CheckPrescriptionValidityHandler,
)
from prescription_service.infrastructure import PrescriptionRepositoryImpl


# Initialize repository
repository = PrescriptionRepositoryImpl()


# ============================================================================
# Command Endpoints
# ============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_prescription(request):
    """Create a new prescription"""
    try:
        data = request.data
        command = CreatePrescriptionCommand(
            customer_id=data['customer_id'],
            prescriber_name=data['prescriber_name'],
            prescriber_license_number=data['prescriber_license_number'],
            prescriber_specialty=data['prescriber_specialty'],
            prescriber_hospital=data['prescriber_hospital'],
            diagnoses=data['diagnoses'],
            validity_days=data.get('validity_days', 90),
            max_refills=data.get('max_refills', 3)
        )
        
        handler = CreatePrescriptionHandler(repository)
        result = handler.handle(command)
        
        return Response(
            {
                "prescription_id": result.prescription_id,
                "customer_id": result.customer_id,
                "status": result.status,
                "created_at": result.created_at.isoformat()
            },
            status=status.HTTP_201_CREATED
        )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_cart_item(request, prescription_id):
    """Add item to prescription cart"""
    try:
        data = request.data
        command = AddCartItemCommand(
            prescription_id=prescription_id,
            product_id=data['product_id'],
            sku=data['sku'],
            product_name=data['product_name'],
            quantity=data['quantity'],
            unit_price=data['unit_price'],
            currency=data.get('currency', 'VND'),
            requires_prescription=data.get('requires_prescription', True),
            frequency=data.get('frequency', ''),
            duration=data.get('duration', ''),
            dosage=data.get('dosage', ''),
            instructions=data.get('instructions', ''),
            warnings=data.get('warnings', '')
        )
        
        handler = AddCartItemHandler(repository)
        result = handler.handle(command)
        
        return Response(
            {
                "prescription_id": result.prescription_id,
                "total_items": result.total_items,
                "total_amount": result.total_amount,
                "operation": result.operation
            },
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_cart_item(request, prescription_id, product_id):
    """Remove item from prescription cart"""
    try:
        command = RemoveCartItemCommand(
            prescription_id=prescription_id,
            product_id=product_id
        )
        
        handler = RemoveCartItemHandler(repository)
        result = handler.handle(command)
        
        return Response(
            {
                "prescription_id": result.prescription_id,
                "total_items": result.total_items,
                "total_amount": result.total_amount,
                "operation": result.operation
            },
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_cart_item_quantity(request, prescription_id, product_id):
    """Update cart item quantity"""
    try:
        data = request.data
        command = UpdateCartItemQuantityCommand(
            prescription_id=prescription_id,
            product_id=product_id,
            new_quantity=data['new_quantity']
        )
        
        handler = UpdateCartItemQuantityHandler(repository)
        result = handler.handle(command)
        
        return Response(
            {
                "prescription_id": result.prescription_id,
                "total_items": result.total_items,
                "total_amount": result.total_amount,
                "operation": result.operation
            },
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_prescription(request, prescription_id):
    """Submit prescription from DRAFT to SUBMITTED"""
    try:
        command = SubmitPrescriptionCommand(prescription_id=prescription_id)
        handler = SubmitPrescriptionHandler(repository)
        result = handler.handle(command)
        
        return Response(
            {
                "prescription_id": result.prescription_id,
                "old_status": result.old_status,
                "new_status": result.new_status,
                "changed_at": result.changed_at.isoformat()
            },
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_prescription(request, prescription_id):
    """Confirm prescription from SUBMITTED to CONFIRMED"""
    try:
        command = ConfirmPrescriptionCommand(prescription_id=prescription_id)
        handler = ConfirmPrescriptionHandler(repository)
        result = handler.handle(command)
        
        return Response(
            {
                "prescription_id": result.prescription_id,
                "old_status": result.old_status,
                "new_status": result.new_status,
                "changed_at": result.changed_at.isoformat()
            },
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def fulfill_prescription_item(request, prescription_id):
    """Fulfill (dispense) a prescription line item"""
    try:
        data = request.data
        command = FulfillPrescriptionItemCommand(
            prescription_id=prescription_id,
            product_id=data['product_id'],
            fulfill_quantity=data['fulfill_quantity']
        )
        
        handler = FulfillPrescriptionItemHandler(repository)
        result = handler.handle(command)
        
        return Response(
            {
                "prescription_id": result.prescription_id,
                "product_id": result.product_id,
                "fulfilled_quantity": result.fulfilled_quantity,
                "remaining_quantity": result.remaining_quantity,
                "fully_fulfilled": result.fully_fulfilled
            },
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_prescription(request, prescription_id):
    """Cancel entire prescription"""
    try:
        data = request.data
        command = CancelPrescriptionCommand(
            prescription_id=prescription_id,
            reason=data.get('reason')
        )
        
        handler = CancelPrescriptionHandler(repository)
        result = handler.handle(command)
        
        return Response(
            {
                "prescription_id": result.prescription_id,
                "old_status": result.old_status,
                "new_status": result.new_status,
                "changed_at": result.changed_at.isoformat()
            },
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def clear_cart(request, prescription_id):
    """Clear all items from prescription cart"""
    try:
        command = ClearCartCommand(prescription_id=prescription_id)
        handler = ClearCartHandler(repository)
        result = handler.handle(command)
        
        return Response(
            {
                "prescription_id": result.prescription_id,
                "total_items": result.total_items,
                "total_amount": result.total_amount,
                "operation": result.operation
            },
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


# ============================================================================
# Query Endpoints
# ============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_prescription_by_id(request, prescription_id):
    """Get prescription by ID"""
    try:
        query = GetPrescriptionByIdQuery(prescription_id=prescription_id)
        handler = GetPrescriptionByIdHandler(repository)
        result = handler.handle(query)
        
        if not result:
            return Response(
                {"error": "Prescription not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(result.__dict__, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_customer_prescriptions(request, customer_id):
    """Get prescriptions for a customer"""
    try:
        limit = request.query_params.get('limit', 20)
        offset = request.query_params.get('offset', 0)
        
        query = GetPrescriptionsByCustomerQuery(
            customer_id=customer_id,
            limit=int(limit),
            offset=int(offset)
        )
        handler = GetPrescriptionsByCustomerHandler(repository)
        result = handler.handle(query)
        
        return Response(
            {
                "items": [item.__dict__ for item in result.items],
                "total_count": result.total_count,
                "limit": result.limit,
                "offset": result.offset
            },
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_prescriptions_by_status(request, status_filter):
    """List prescriptions by status"""
    try:
        limit = request.query_params.get('limit', 20)
        offset = request.query_params.get('offset', 0)
        
        query = ListPrescriptionsByStatusQuery(
            status=status_filter,
            limit=int(limit),
            offset=int(offset)
        )
        handler = ListPrescriptionsByStatusHandler(repository)
        result = handler.handle(query)
        
        return Response(
            {
                "items": [item.__dict__ for item in result.items],
                "total_count": result.total_count,
                "limit": result.limit,
                "offset": result.offset
            },
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_draft_prescriptions(request):
    """List draft prescriptions"""
    try:
        limit = request.query_params.get('limit', 20)
        offset = request.query_params.get('offset', 0)
        
        query = ListDraftPrescriptionsQuery(
            limit=int(limit),
            offset=int(offset)
        )
        handler = ListDraftPrescriptionsHandler(repository)
        result = handler.handle(query)
        
        return Response(
            {
                "items": [item.__dict__ for item in result.items],
                "total_count": result.total_count,
                "limit": result.limit,
                "offset": result.offset
            },
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_submitted_prescriptions(request):
    """List submitted prescriptions"""
    try:
        limit = request.query_params.get('limit', 20)
        offset = request.query_params.get('offset', 0)
        
        query = ListSubmittedPrescriptionsQuery(
            limit=int(limit),
            offset=int(offset)
        )
        handler = ListSubmittedPrescriptionsHandler(repository)
        result = handler.handle(query)
        
        return Response(
            {
                "items": [item.__dict__ for item in result.items],
                "total_count": result.total_count,
                "limit": result.limit,
                "offset": result.offset
            },
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_active_prescriptions(request):
    """List active prescriptions"""
    try:
        limit = request.query_params.get('limit', 20)
        offset = request.query_params.get('offset', 0)
        
        query = ListActivePrescriptionsQuery(
            limit=int(limit),
            offset=int(offset)
        )
        handler = ListActivePrescriptionsHandler(repository)
        result = handler.handle(query)
        
        return Response(
            {
                "items": [item.__dict__ for item in result.items],
                "total_count": result.total_count,
                "limit": result.limit,
                "offset": result.offset
            },
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_recent_prescriptions(request):
    """List recent prescriptions"""
    try:
        days = request.query_params.get('days', 7)
        limit = request.query_params.get('limit', 20)
        offset = request.query_params.get('offset', 0)
        
        query = ListRecentPrescriptionsQuery(
            days=int(days),
            limit=int(limit),
            offset=int(offset)
        )
        handler = ListRecentPrescriptionsHandler(repository)
        result = handler.handle(query)
        
        return Response(
            {
                "items": [item.__dict__ for item in result.items],
                "total_count": result.total_count,
                "limit": result.limit,
                "offset": result.offset
            },
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_prescriptions(request):
    """Search prescriptions by customer and optional status"""
    try:
        customer_id = request.query_params.get('customer_id')
        status_filter = request.query_params.get('status')
        limit = request.query_params.get('limit', 20)
        offset = request.query_params.get('offset', 0)
        
        query = SearchPrescriptionQuery(
            customer_id=customer_id,
            status=status_filter,
            limit=int(limit),
            offset=int(offset)
        )
        handler = SearchPrescriptionHandler(repository)
        result = handler.handle(query)
        
        return Response(
            {
                "items": [item.__dict__ for item in result.items],
                "total_count": result.total_count,
                "limit": result.limit,
                "offset": result.offset
            },
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_prescription_items(request, prescription_id):
    """Get line items for a prescription"""
    try:
        query = GetPrescriptionItemsQuery(prescription_id=prescription_id)
        handler = GetPrescriptionItemsHandler(repository)
        result = handler.handle(query)
        
        return Response(
            {"items": [item.__dict__ for item in result]},
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_prescription_validity(request, prescription_id):
    """Check if prescription is valid"""
    try:
        query = CheckPrescriptionValidityQuery(prescription_id=prescription_id)
        handler = CheckPrescriptionValidityHandler(repository)
        result = handler.handle(query)
        
        return Response(
            {
                "prescription_id": result.prescription_id,
                "is_valid": result.is_valid,
                "status": result.status,
                "days_remaining": result.days_remaining,
                "message": result.message
            },
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
