"""
Patient Interface Layer - HTTP Views (Django)

These are thin HTTP controllers that:
- Accept HTTP requests
- Call appropriate command/query handlers
- Return HTTP responses

They should NOT contain business logic.
All business logic should be in the application or domain layers.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import datetime

from ...infrastructure import PatientRepositoryImpl
from ...application import (
    RegisterPatientCommand, RegisterPatientCommandHandler,
    UpdatePatientInsuranceCommand, UpdatePatientInsuranceCommandHandler,
    UpdatePatientContactCommand, UpdatePatientContactCommandHandler,
    UpdatePatientAddressCommand, UpdatePatientAddressCommandHandler,
    GetPatientByIdQuery, GetPatientByIdQueryHandler,
    GetPatientByAccountIdQuery, GetPatientByAccountIdQueryHandler,
    ListAllPatientsQuery, ListAllPatientsQueryHandler,
    ListInsuredPatientsQuery, ListInsuredPatientsQueryHandler,
    GetPatientMedicalRecordsQuery, GetPatientMedicalRecordsQueryHandler,
)


# Repository singleton (in production, use dependency injection)
patient_repo = PatientRepositoryImpl()


@csrf_exempt
@require_http_methods(["POST"])
def register_patient(request):
    """
    HTTP POST /patients/register
    
    Register a new patient
    """
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required = ['account_id', 'full_name', 'email', 'phone', 'date_of_birth', 'gender']
        if not all(k in data for k in required):
            return JsonResponse(
                {"error": f"Missing required fields: {required}"},
                status=400
            )
        
        # Create command
        command = RegisterPatientCommand(
            account_id=data['account_id'],
            full_name=data['full_name'],
            email=data['email'],
            phone=data['phone'],
            date_of_birth=datetime.fromisoformat(data['date_of_birth']),
            gender=data['gender'],
            blood_type=data.get('blood_type'),
        )
        
        # Execute command
        handler = RegisterPatientCommandHandler(patient_repo)
        result = handler.handle(command)
        
        if result['success']:
            return JsonResponse(result, status=201)
        else:
            return JsonResponse(result, status=400)
    
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
def get_patient(request, patient_id):
    """
    HTTP GET /patients/{patient_id}
    
    Get patient by ID
    """
    try:
        query = GetPatientByIdQuery(patient_id=patient_id)
        handler = GetPatientByIdQueryHandler(patient_repo)
        result = handler.handle(query)
        
        if not result:
            return JsonResponse({"error": "Patient not found"}, status=404)
        
        return JsonResponse(result, status=200)
    
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
def get_patient_by_account(request, account_id):
    """
    HTTP GET /patients/account/{account_id}
    
    Get patient by account ID
    """
    try:
        query = GetPatientByAccountIdQuery(account_id=account_id)
        handler = GetPatientByAccountIdQueryHandler(patient_repo)
        result = handler.handle(query)
        
        if not result:
            return JsonResponse({"error": "Patient not found"}, status=404)
        
        return JsonResponse(result, status=200)
    
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
def list_patients(request):
    """
    HTTP GET /patients?page=1&page_size=20
    
    List all patients with pagination
    """
    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        
        query = ListAllPatientsQuery(page=page, page_size=page_size)
        handler = ListAllPatientsQueryHandler(patient_repo)
        result = handler.handle(query)
        
        return JsonResponse(result, status=200)
    
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
def list_insured_patients(request):
    """
    HTTP GET /patients/insured?page=1&page_size=20
    
    List patients with valid insurance
    """
    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        
        query = ListInsuredPatientsQuery(page=page, page_size=page_size)
        handler = ListInsuredPatientsQueryHandler(patient_repo)
        result = handler.handle(query)
        
        return JsonResponse(result, status=200)
    
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["PUT"])
def update_insurance(request, patient_id):
    """
    HTTP PUT /patients/{patient_id}/insurance
    
    Update patient's insurance
    """
    try:
        data = json.loads(request.body)
        
        command = UpdatePatientInsuranceCommand(
            patient_id=patient_id,
            insurance_code=data['insurance_code'],
            discount_rate=data.get('discount_rate', 0.8),
            valid_days=data.get('valid_days', 365),
        )
        
        handler = UpdatePatientInsuranceCommandHandler(patient_repo)
        result = handler.handle(command)
        
        if result['success']:
            return JsonResponse(result, status=200)
        else:
            return JsonResponse(result, status=400)
    
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["PUT"])
def update_contact(request, patient_id):
    """
    HTTP PUT /patients/{patient_id}/contact
    
    Update patient's contact information
    """
    try:
        data = json.loads(request.body)
        
        command = UpdatePatientContactCommand(
            patient_id=patient_id,
            email=data.get('email'),
            phone=data.get('phone'),
        )
        
        handler = UpdatePatientContactCommandHandler(patient_repo)
        result = handler.handle(command)
        
        if result['success']:
            return JsonResponse(result, status=200)
        else:
            return JsonResponse(result, status=400)
    
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["PUT"])
def update_address(request, patient_id):
    """
    HTTP PUT /patients/{patient_id}/address
    
    Update patient's address
    """
    try:
        data = json.loads(request.body)
        
        required = ['street', 'ward', 'district', 'province', 'postal_code']
        if not all(k in data for k in required):
            return JsonResponse(
                {"error": f"Missing required fields: {required}"},
                status=400
            )
        
        command = UpdatePatientAddressCommand(
            patient_id=patient_id,
            street=data['street'],
            ward=data['ward'],
            district=data['district'],
            province=data['province'],
            postal_code=data['postal_code'],
        )
        
        handler = UpdatePatientAddressCommandHandler(patient_repo)
        result = handler.handle(command)
        
        if result['success']:
            return JsonResponse(result, status=200)
        else:
            return JsonResponse(result, status=400)
    
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
def get_medical_records(request, patient_id):
    """
    HTTP GET /patients/{patient_id}/medical-records
    
    Get patient's medical records
    """
    try:
        query = GetPatientMedicalRecordsQuery(patient_id=patient_id)
        handler = GetPatientMedicalRecordsQueryHandler(patient_repo)
        result = handler.handle(query)
        
        return JsonResponse({"records": result}, status=200)
    
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
