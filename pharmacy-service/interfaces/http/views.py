"""
Pharmacy Interface Layer - HTTP Controllers (Django Views)
Thin controllers that delegate to application layer handlers
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

import json
from datetime import datetime
from decimal import Decimal

from django.http import JsonResponse
from django.views import View
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator

from application import (
    # Commands
    CreateProductCommand,
    ReceiveInventoryCommand,
    SellProductCommand,
    ScrapProductCommand,
    ChangePriceCommand,
    AdjustMinStockCommand,
    ChangeManufacturerCommand,
    CheckExpiringProductsCommand,
    DeactivateProductCommand,
    # Command Handlers
    CreateProductCommandHandler,
    ReceiveInventoryCommandHandler,
    SellProductCommandHandler,
    ScrapProductCommandHandler,
    ChangePriceCommandHandler,
    AdjustMinStockCommandHandler,
    ChangeManufacturerCommandHandler,
    CheckExpiringProductsCommandHandler,
    DeactivateProductCommandHandler,
    # Queries
    GetProductByIdQuery,
    GetProductBySKUQuery,
    GetProductByATCQuery,
    ListAllProductsQuery,
    ListActiveProductsQuery,
    ListLowStockProductsQuery,
    SearchProductsQuery,
    GetProductsByCategoryQuery,
    GetProductInventoryQuery,
    GetExpiringProductsQuery,
    # Query Handlers
    GetProductByIdQueryHandler,
    GetProductBySKUQueryHandler,
    GetProductByATCQueryHandler,
    ListAllProductsQueryHandler,
    ListActiveProductsQueryHandler,
    ListLowStockProductsQueryHandler,
    SearchProductsQueryHandler,
    GetProductsByCategoryQueryHandler,
    GetProductInventoryQueryHandler,
    GetExpiringProductsQueryHandler,
)

from infrastructure import ProductRepositoryImpl


# Initialize repository (in production, use dependency injection)
product_repo = ProductRepositoryImpl()


def parse_json_body(request):
    """Parse JSON request body"""
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
# COMMAND ENDPOINTS (POST requests for state changes)
# ============================================================================

@require_http_methods(["POST"])
def create_product(request):
    """
    POST /api/products/create
    Create new product inventory item
    """
    body = parse_json_body(request)
    if not body:
        return error_response("Invalid JSON body")
    
    try:
        command = CreateProductCommand(
            sku=body.get("sku"),
            generic_name=body.get("generic_name"),
            trade_name=body.get("trade_name"),
            dosage_form=body.get("dosage_form"),
            dosage_strength=body.get("dosage_strength"),
            manufacturer_name=body.get("manufacturer_name"),
            manufacturer_country=body.get("manufacturer_country"),
            price_amount=float(body.get("price_amount", 0)),
            price_currency=body.get("price_currency", "VND"),
            atc_code=body.get("atc_code"),
            icd_codes=body.get("icd_codes", []),
            category=body.get("category"),
            requires_prescription=body.get("requires_prescription", False),
            description=body.get("description", ""),
            min_stock_level=int(body.get("min_stock_level", 10)),
            reorder_point=int(body.get("reorder_point", 20)),
        )
        
        handler = CreateProductCommandHandler(product_repo)
        result = handler.handle(command)
        
        return success_response(result, status=201)
    
    except Exception as e:
        return error_response(f"Error creating product: {str(e)}", status=400)


@require_http_methods(["POST"])
def receive_inventory(request):
    """
    POST /api/products/<product_id>/receive
    Receive new inventory batch for product
    """
    body = parse_json_body(request)
    if not body:
        return error_response("Invalid JSON body")
    
    try:
        product_id = request.POST.get("product_id") or body.get("product_id")
        
        command = ReceiveInventoryCommand(
            product_id=product_id,
            batch_number=body.get("batch_number"),
            quantity=int(body.get("quantity", 0)),
            unit=body.get("unit", "box"),
            expiry_date=body.get("expiry_date"),
        )
        
        handler = ReceiveInventoryCommandHandler(product_repo)
        result = handler.handle(command)
        
        return success_response(result)
    
    except Exception as e:
        return error_response(f"Error receiving inventory: {str(e)}", status=400)


@require_http_methods(["POST"])
def sell_product(request):
    """
    POST /api/products/<product_id>/sell
    Remove inventory when product is sold/dispensed
    """
    body = parse_json_body(request)
    if not body:
        return error_response("Invalid JSON body")
    
    try:
        product_id = request.POST.get("product_id") or body.get("product_id")
        
        command = SellProductCommand(
            product_id=product_id,
            quantity=int(body.get("quantity", 0)),
            reason=body.get("reason", "sale"),
        )
        
        handler = SellProductCommandHandler(product_repo)
        result = handler.handle(command)
        
        return success_response(result)
    
    except Exception as e:
        return error_response(f"Error selling product: {str(e)}", status=400)


@require_http_methods(["POST"])
def scrap_product(request):
    """
    POST /api/products/<product_id>/scrap
    Mark inventory as scrapped (expired, damaged, etc)
    """
    body = parse_json_body(request)
    if not body:
        return error_response("Invalid JSON body")
    
    try:
        product_id = request.POST.get("product_id") or body.get("product_id")
        
        command = ScrapProductCommand(
            product_id=product_id,
            batch_number=body.get("batch_number"),
            quantity=int(body.get("quantity", 0)),
            reason=body.get("reason", "unknown"),
        )
        
        handler = ScrapProductCommandHandler(product_repo)
        result = handler.handle(command)
        
        return success_response(result)
    
    except Exception as e:
        return error_response(f"Error scrapping product: {str(e)}", status=400)


@require_http_methods(["POST"])
def change_price(request):
    """
    POST /api/products/<product_id>/price
    Update product price
    """
    body = parse_json_body(request)
    if not body:
        return error_response("Invalid JSON body")
    
    try:
        product_id = request.POST.get("product_id") or body.get("product_id")
        
        command = ChangePriceCommand(
            product_id=product_id,
            price_amount=float(body.get("price_amount", 0)),
            price_currency=body.get("price_currency", "VND"),
            reason=body.get("reason", "price_update"),
        )
        
        handler = ChangePriceCommandHandler(product_repo)
        result = handler.handle(command)
        
        return success_response(result)
    
    except Exception as e:
        return error_response(f"Error changing price: {str(e)}", status=400)


@require_http_methods(["POST"])
def adjust_min_stock(request):
    """
    POST /api/products/<product_id>/min-stock
    Adjust minimum stock level
    """
    body = parse_json_body(request)
    if not body:
        return error_response("Invalid JSON body")
    
    try:
        product_id = request.POST.get("product_id") or body.get("product_id")
        
        command = AdjustMinStockCommand(
            product_id=product_id,
            new_min_stock_level=int(body.get("new_min_stock_level", 10)),
            new_reorder_point=int(body.get("new_reorder_point", 20)),
        )
        
        handler = AdjustMinStockCommandHandler(product_repo)
        result = handler.handle(command)
        
        return success_response(result)
    
    except Exception as e:
        return error_response(f"Error adjusting min stock: {str(e)}", status=400)


@require_http_methods(["POST"])
def change_manufacturer(request):
    """
    POST /api/products/<product_id>/manufacturer
    Change product manufacturer
    """
    body = parse_json_body(request)
    if not body:
        return error_response("Invalid JSON body")
    
    try:
        product_id = request.POST.get("product_id") or body.get("product_id")
        
        command = ChangeManufacturerCommand(
            product_id=product_id,
            manufacturer_name=body.get("manufacturer_name"),
            manufacturer_country=body.get("manufacturer_country"),
        )
        
        handler = ChangeManufacturerCommandHandler(product_repo)
        result = handler.handle(command)
        
        return success_response(result)
    
    except Exception as e:
        return error_response(f"Error changing manufacturer: {str(e)}", status=400)


@require_http_methods(["POST"])
def check_expiring_products(request):
    """
    POST /api/products/check-expiring
    Check for products expiring soon
    """
    body = parse_json_body(request)
    days_threshold = int(body.get("days_threshold", 30)) if body else 30
    
    try:
        command = CheckExpiringProductsCommand(
            days_threshold=days_threshold,
        )
        
        handler = CheckExpiringProductsCommandHandler(product_repo)
        result = handler.handle(command)
        
        return success_response(result)
    
    except Exception as e:
        return error_response(f"Error checking expiring products: {str(e)}", status=400)


@require_http_methods(["POST"])
def deactivate_product(request):
    """
    POST /api/products/<product_id>/deactivate
    Deactivate product (mark as no longer available)
    """
    body = parse_json_body(request)
    if not body:
        return error_response("Invalid JSON body")
    
    try:
        product_id = request.POST.get("product_id") or body.get("product_id")
        
        command = DeactivateProductCommand(
            product_id=product_id,
            reason=body.get("reason", "unknown"),
        )
        
        handler = DeactivateProductCommandHandler(product_repo)
        result = handler.handle(command)
        
        return success_response(result)
    
    except Exception as e:
        return error_response(f"Error deactivating product: {str(e)}", status=400)


# ============================================================================
# QUERY ENDPOINTS (GET requests for reading data)
# ============================================================================

@require_http_methods(["GET"])
def get_product_by_id(request, product_id):
    """
    GET /api/products/<product_id>
    Retrieve product by ID
    """
    try:
        query = GetProductByIdQuery(product_id=product_id)
        handler = GetProductByIdQueryHandler(product_repo)
        result = handler.handle(query)
        
        if not result:
            return error_response("Product not found", status=404)
        
        return success_response(result)
    
    except Exception as e:
        return error_response(f"Error fetching product: {str(e)}", status=400)


@require_http_methods(["GET"])
def get_product_by_sku(request, sku):
    """
    GET /api/products/sku/<sku>
    Retrieve product by SKU
    """
    try:
        query = GetProductBySKUQuery(sku=sku)
        handler = GetProductBySKUQueryHandler(product_repo)
        result = handler.handle(query)
        
        if not result:
            return error_response("Product not found", status=404)
        
        return success_response(result)
    
    except Exception as e:
        return error_response(f"Error fetching product: {str(e)}", status=400)


@require_http_methods(["GET"])
def get_products_by_atc(request, atc_code):
    """
    GET /api/products/atc/<atc_code>
    Retrieve all products with given ATC code
    """
    try:
        query = GetProductByATCQuery(atc_code=atc_code)
        handler = GetProductByATCQueryHandler(product_repo)
        result = handler.handle(query)
        
        return success_response({
            "atc_code": atc_code,
            "products": result,
            "count": len(result),
        })
    
    except Exception as e:
        return error_response(f"Error fetching products: {str(e)}", status=400)


@require_http_methods(["GET"])
def list_all_products(request):
    """
    GET /api/products
    List all products with pagination
    """
    try:
        page = int(request.GET.get("page", 1))
        page_size = int(request.GET.get("page_size", 20))
        
        query = ListAllProductsQuery(page=page, page_size=page_size)
        handler = ListAllProductsQueryHandler(product_repo)
        result = handler.handle(query)
        
        return success_response(result)
    
    except Exception as e:
        return error_response(f"Error fetching products: {str(e)}", status=400)


@require_http_methods(["GET"])
def list_active_products(request):
    """
    GET /api/products/active
    List all active products
    """
    try:
        page = int(request.GET.get("page", 1))
        page_size = int(request.GET.get("page_size", 20))
        
        query = ListActiveProductsQuery(page=page, page_size=page_size)
        handler = ListActiveProductsQueryHandler(product_repo)
        result = handler.handle(query)
        
        return success_response(result)
    
    except Exception as e:
        return error_response(f"Error fetching products: {str(e)}", status=400)


@require_http_methods(["GET"])
def list_low_stock_products(request):
    """
    GET /api/products/low-stock
    List products with low inventory
    """
    try:
        page = int(request.GET.get("page", 1))
        page_size = int(request.GET.get("page_size", 20))
        threshold = int(request.GET.get("threshold", 0))
        
        query = ListLowStockProductsQuery(
            page=page,
            page_size=page_size,
            threshold=threshold
        )
        handler = ListLowStockProductsQueryHandler(product_repo)
        result = handler.handle(query)
        
        return success_response(result)
    
    except Exception as e:
        return error_response(f"Error fetching products: {str(e)}", status=400)


@require_http_methods(["GET"])
def search_products(request):
    """
    GET /api/products/search?q=<search_term>
    Search products by name
    """
    try:
        search_term = request.GET.get("q", "")
        page = int(request.GET.get("page", 1))
        page_size = int(request.GET.get("page_size", 20))
        
        query = SearchProductsQuery(
            search_term=search_term,
            page=page,
            page_size=page_size
        )
        handler = SearchProductsQueryHandler(product_repo)
        result = handler.handle(query)
        
        return success_response(result)
    
    except Exception as e:
        return error_response(f"Error searching products: {str(e)}", status=400)


@require_http_methods(["GET"])
def get_products_by_category(request, category):
    """
    GET /api/products/category/<category>
    Retrieve products by category
    """
    try:
        page = int(request.GET.get("page", 1))
        page_size = int(request.GET.get("page_size", 20))
        
        query = GetProductsByCategoryQuery(
            category=category,
            page=page,
            page_size=page_size
        )
        handler = GetProductsByCategoryQueryHandler(product_repo)
        result = handler.handle(query)
        
        return success_response(result)
    
    except Exception as e:
        return error_response(f"Error fetching products: {str(e)}", status=400)


@require_http_methods(["GET"])
def get_product_inventory(request, product_id):
    """
    GET /api/products/<product_id>/inventory
    Get detailed inventory information for product
    """
    try:
        query = GetProductInventoryQuery(product_id=product_id)
        handler = GetProductInventoryQueryHandler(product_repo)
        result = handler.handle(query)
        
        if not result:
            return error_response("Product not found", status=404)
        
        return success_response(result)
    
    except Exception as e:
        return error_response(f"Error fetching inventory: {str(e)}", status=400)


@require_http_methods(["GET"])
def get_expiring_products(request):
    """
    GET /api/products/expiring?days=<days>
    Get products expiring soon
    """
    try:
        days_threshold = int(request.GET.get("days", 30))
        page = int(request.GET.get("page", 1))
        page_size = int(request.GET.get("page_size", 20))
        
        query = GetExpiringProductsQuery(
            days_threshold=days_threshold,
            page=page,
            page_size=page_size
        )
        handler = GetExpiringProductsQueryHandler(product_repo)
        result = handler.handle(query)
        
        return success_response(result)
    
    except Exception as e:
        return error_response(f"Error fetching expiring products: {str(e)}", status=400)


@require_http_methods(["GET"])
def health_check(request):
    """
    GET /api/products/health
    Health check endpoint
    """
    return success_response({"status": "healthy", "service": "pharmacy"})
