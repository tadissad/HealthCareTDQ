"""
Patient Service - Unit Tests for Domain Layer

Examples of how to test domain logic independently of Django/Database
"""

import pytest
from datetime import datetime, timedelta

# These tests assume you're using pytest with pytest-django

# ============================================================================
# VALUE OBJECT TESTS
# ============================================================================

class TestPatientIdValueObject:
    def test_patient_id_creation(self):
        from patient_service.domain import PatientId
        patient_id = PatientId("PAT_001")
        assert str(patient_id) == "PAT_001"
    
    def test_patient_id_equality(self):
        from patient_service.domain import PatientId
        id1 = PatientId("PAT_001")
        id2 = PatientId("PAT_001")
        id3 = PatientId("PAT_002")
        
        assert id1 == id2
        assert id1 != id3


class TestEmailValueObject:
    def test_valid_email(self):
        from patient_service.domain import Email
        email = Email("user@example.com")
        assert email.value == "user@example.com"
    
    def test_invalid_email_raises_error(self):
        from patient_service.domain import Email
        from shared_ddd.base import InvalidValueObjectException
        
        with pytest.raises(InvalidValueObjectException):
            Email("invalid-email")


class TestInsuranceValueObject:
    def test_valid_insurance(self):
        from patient_service.domain import Insurance
        valid_until = datetime.now() + timedelta(days=365)
        insurance = Insurance(
            code="BHYT_001",
            discount_rate=0.8,
            valid_until=valid_until
        )
        assert insurance.code == "BHYT_001"
        assert insurance.discount_rate == 0.8
    
    def test_expired_insurance_raises_error(self):
        from patient_service.domain import Insurance
        from shared_ddd.base import InvalidValueObjectException
        
        expired = datetime.now() - timedelta(days=1)
        with pytest.raises(InvalidValueObjectException):
            Insurance("BHYT_001", 0.8, expired)
    
    def test_insurance_discount_calculation(self):
        from patient_service.domain import Insurance
        valid_until = datetime.now() + timedelta(days=365)
        insurance = Insurance("BHYT_001", 0.8, valid_until)
        
        # Treatment cost: 1000 VND
        # Patient pays: 20% = 200 VND
        patient_payment = insurance.calculate_patient_payment(1000)
        assert patient_payment == 200
        
        # Insurance pays: 80% = 800 VND
        insurance_payment = insurance.calculate_insured_amount(1000)
        assert insurance_payment == 800


# ============================================================================
# ENTITY & AGGREGATE TESTS
# ============================================================================

class TestPatientAggregate:
    def test_patient_creation_raises_event(self):
        from patient_service.domain import (
            Patient, PatientId, Email, Phone, PatientRegistered
        )
        
        patient_id = PatientId("PAT_001")
        patient = Patient(
            id=patient_id,
            account_id="ACC_001",
            full_name="Nguyễn Văn A",
            email=Email("a@example.com"),
            phone=Phone("0987654321"),
            date_of_birth=datetime(1990, 1, 1),
            gender="Male"
        )
        
        # Check event was raised
        events = patient.get_events()
        assert len(events) == 1
        assert isinstance(events[0], PatientRegistered)
        assert events[0].name == "Nguyễn Văn A"
    
    def test_patient_register_insurance(self):
        from patient_service.domain import (
            Patient, PatientId, Email, Phone, Insurance, InsuranceUpdated
        )
        
        patient_id = PatientId("PAT_001")
        patient = Patient(
            id=patient_id,
            account_id="ACC_001",
            full_name="Nguyễn Văn A",
            email=Email("a@example.com"),
            phone=Phone("0987654321"),
            date_of_birth=datetime(1990, 1, 1),
            gender="Male"
        )
        
        # Clear initial event
        patient.clear_events()
        
        # Register insurance
        valid_until = datetime.now() + timedelta(days=365)
        insurance = Insurance("BHYT_001", 0.8, valid_until)
        patient.register_insurance(insurance)
        
        # Check insurance was set
        assert patient.insurance is not None
        assert patient.insurance.code == "BHYT_001"
        
        # Check event was raised
        events = patient.get_events()
        assert len(events) == 1
        assert isinstance(events[0], InsuranceUpdated)
    
    def test_patient_is_insured(self):
        from patient_service.domain import Patient, PatientId, Email, Phone, Insurance
        
        patient_id = PatientId("PAT_001")
        patient = Patient(
            id=patient_id,
            account_id="ACC_001",
            full_name="Nguyễn Văn A",
            email=Email("a@example.com"),
            phone=Phone("0987654321"),
            date_of_birth=datetime(1990, 1, 1),
            gender="Male"
        )
        
        assert not patient.is_insured()
        
        # Add insurance
        valid_until = datetime.now() + timedelta(days=365)
        insurance = Insurance("BHYT_001", 0.8, valid_until)
        patient.register_insurance(insurance)
        
        assert patient.is_insured()
    
    def test_patient_calculate_treatment_cost(self):
        from patient_service.domain import Patient, PatientId, Email, Phone, Insurance, Money
        
        patient_id = PatientId("PAT_001")
        patient = Patient(
            id=patient_id,
            account_id="ACC_001",
            full_name="Nguyễn Văn A",
            email=Email("a@example.com"),
            phone=Phone("0987654321"),
            date_of_birth=datetime(1990, 1, 1),
            gender="Male"
        )
        
        # Without insurance
        base_cost = Money(1000)
        cost_breakdown = patient.calculate_treatment_cost(base_cost)
        assert cost_breakdown["patient_payment"] == 1000
        assert cost_breakdown["insurance_payment"] == 0
        
        # With insurance
        valid_until = datetime.now() + timedelta(days=365)
        insurance = Insurance("BHYT_001", 0.8, valid_until)
        patient.register_insurance(insurance)
        
        cost_breakdown = patient.calculate_treatment_cost(base_cost)
        assert cost_breakdown["patient_payment"] == 200  # 20%
        assert cost_breakdown["insurance_payment"] == 800  # 80%
    
    def test_patient_get_age(self):
        from patient_service.domain import Patient, PatientId, Email, Phone
        
        patient_id = PatientId("PAT_001")
        
        # Born 25 years ago
        birth_date = datetime.now() - timedelta(days=25*365)
        
        patient = Patient(
            id=patient_id,
            account_id="ACC_001",
            full_name="Nguyễn Văn A",
            email=Email("a@example.com"),
            phone=Phone("0987654321"),
            date_of_birth=birth_date,
            gender="Male"
        )
        
        age = patient.get_age()
        assert age == 25


# ============================================================================
# DOMAIN SERVICE TESTS
# ============================================================================

class TestPatientRegistrationService:
    """Test domain service - requires repository mock"""
    
    @pytest.fixture
    def mock_repo(self):
        """Create a mock repository"""
        from unittest.mock import Mock
        return Mock()
    
    def test_register_new_patient(self, mock_repo):
        from patient_service.domain import PatientRegistrationService
        
        service = PatientRegistrationService(mock_repo)
        
        patient = service.register_new_patient(
            account_id="ACC_001",
            full_name="Nguyễn Văn A",
            email="a@example.com",
            phone="0987654321",
            date_of_birth=datetime(1990, 1, 1),
            gender="Male",
            blood_type="O",
        )
        
        assert patient.full_name == "Nguyễn Văn A"
        assert patient.email.value == "a@example.com"
        assert patient.phone.value == "987654321"  # Cleaned
        assert patient.blood_type.value == "O"
        
        # Check repository.add was called
        mock_repo.add.assert_called_once()
    
    def test_issue_insurance(self, mock_repo):
        from patient_service.domain import (
            PatientRegistrationService, PatientId, Patient, Email, Phone
        )
        
        # Create existing patient
        patient_id = PatientId("PAT_001")
        existing_patient = Patient(
            id=patient_id,
            account_id="ACC_001",
            full_name="Trần Thị B",
            email=Email("b@example.com"),
            phone=Phone("0987654322"),
            date_of_birth=datetime(1995, 1, 1),
            gender="Female",
        )
        
        mock_repo.get_by_id.return_value = existing_patient
        
        service = PatientRegistrationService(mock_repo)
        
        service.issue_insurance(
            patient_id=patient_id,
            insurance_code="BHYT_001",
            discount_rate=0.8,
            valid_days=365,
        )
        
        # Check insurance was added
        assert existing_patient.insurance is not None
        assert existing_patient.insurance.code == "BHYT_001"
        
        # Check repository.update was called
        mock_repo.update.assert_called_once()


# ============================================================================
# INTEGRATION TESTS (with database mocking)
# ============================================================================

@pytest.mark.django_db
class TestPatientRepositoryIntegration:
    """Integration tests - uses actual repository with test database"""
    
    def test_save_and_retrieve_patient(self):
        from patient_service.infrastructure import PatientRepositoryImpl
        from patient_service.domain import PatientId, Email, Phone, Patient
        
        repo = PatientRepositoryImpl()
        
        # Create patient
        patient_id = PatientId("PAT_TEST_001")
        patient = Patient(
            id=patient_id,
            account_id="ACC_TEST_001",
            full_name="Test Patient",
            email=Email("test@example.com"),
            phone=Phone("0987654321"),
            date_of_birth=datetime(1990, 1, 1),
            gender="Male",
        )
        
        # Save
        repo.add(patient)
        
        # Retrieve
        retrieved = repo.get_by_id(patient_id)
        
        assert retrieved is not None
        assert retrieved.full_name == "Test Patient"
        assert retrieved.email.value == "test@example.com"
        assert retrieved.phone.value == "987654321"


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    # Run all tests
    pytest.main([__file__, "-v"])
    
    # Or run specific test class
    # pytest.main([__file__ + "::TestPatientAggregate", "-v"])
