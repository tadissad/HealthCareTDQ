"""
Patient Application Layer - Queries

Queries represent read-only requests that don't modify state.
They return DTOs (Data Transfer Objects), not domain entities.
"""

from dataclasses import dataclass


@dataclass
class GetPatientByIdQuery:
    """Query: Get patient by ID"""
    patient_id: str


@dataclass
class GetPatientByAccountIdQuery:
    """Query: Get patient by account ID"""
    account_id: str


@dataclass
class GetPatientByEmailQuery:
    """Query: Get patients by email"""
    email: str


@dataclass
class ListAllPatientsQuery:
    """Query: Get all patients with pagination"""
    page: int = 1
    page_size: int = 20


@dataclass
class ListInsuredPatientsQuery:
    """Query: Get all patients with valid insurance"""
    page: int = 1
    page_size: int = 20


@dataclass
class GetPatientMedicalRecordsQuery:
    """Query: Get patient's medical records"""
    patient_id: str
