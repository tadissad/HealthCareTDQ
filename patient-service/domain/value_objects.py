"""
Patient Domain - Value Objects
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import re

# Import base classes
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))
from shared_ddd.base import ValueObject, InvalidValueObjectException


@dataclass
class PatientId(ValueObject):
    """Unique identifier for a patient"""
    value: str
    
    def equals(self, other: "PatientId") -> bool:
        return self.value == other.value
    
    def __str__(self):
        return self.value
    
    def __hash__(self):
        return hash(self.value)


@dataclass
class Email(ValueObject):
    """Email value object with validation"""
    value: str
    
    def __post_init__(self):
        if not self._is_valid_email(self.value):
            raise InvalidValueObjectException(f"Invalid email: {self.value}")
    
    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """Basic email validation"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def equals(self, other: "Email") -> bool:
        return self.value.lower() == other.value.lower()
    
    def __str__(self):
        return self.value


@dataclass
class Phone(ValueObject):
    """Phone number value object"""
    value: str
    
    def __post_init__(self):
        # Remove all non-digit characters and validate
        cleaned = ''.join(c for c in self.value if c.isdigit())
        if len(cleaned) < 9:
            raise InvalidValueObjectException(f"Invalid phone: {self.value}")
        self.value = cleaned
    
    def equals(self, other: "Phone") -> bool:
        return self.value == other.value
    
    def __str__(self):
        return self.value


@dataclass
class Insurance(ValueObject):
    """Health insurance information (BHYT - Bảo Hiểm Y Tế)"""
    code: str
    discount_rate: float  # 0.8 means patient pays 20%, insurance covers 80%
    valid_until: datetime
    
    def __post_init__(self):
        if not (0 <= self.discount_rate <= 1):
            raise InvalidValueObjectException(f"Invalid discount_rate: {self.discount_rate}")
        if self.valid_until <= datetime.now():
            raise InvalidValueObjectException(f"Insurance expired: {self.valid_until}")
    
    def equals(self, other: "Insurance") -> bool:
        return self.code == other.code and self.valid_until == other.valid_until
    
    def is_valid(self) -> bool:
        """Check if insurance is still valid"""
        return datetime.now() <= self.valid_until
    
    def calculate_patient_payment(self, treatment_cost: float) -> float:
        """Calculate amount patient must pay after insurance discount"""
        return treatment_cost * (1 - self.discount_rate)
    
    def calculate_insured_amount(self, treatment_cost: float) -> float:
        """Calculate amount insurance covers"""
        return treatment_cost * self.discount_rate


@dataclass
class Address(ValueObject):
    """Patient's address"""
    street: str
    ward: str
    district: str
    province: str
    postal_code: str
    
    def equals(self, other: "Address") -> bool:
        return (self.street == other.street and
                self.ward == other.ward and
                self.district == other.district and
                self.province == other.province and
                self.postal_code == other.postal_code)
    
    def __str__(self):
        return f"{self.street}, {self.ward}, {self.district}, {self.province}, {self.postal_code}"


@dataclass
class BloodType(ValueObject):
    """Blood type value object"""
    value: str
    
    def __post_init__(self):
        valid_types = {"O", "A", "B", "AB", "O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-"}
        if self.value not in valid_types:
            raise InvalidValueObjectException(f"Invalid blood type: {self.value}")
    
    def equals(self, other: "BloodType") -> bool:
        return self.value == other.value


@dataclass
class Money(ValueObject):
    """Money value object with currency"""
    amount: float
    currency: str = "VND"
    
    def __post_init__(self):
        if self.amount < 0:
            raise InvalidValueObjectException(f"Invalid amount: {self.amount}")
    
    def equals(self, other: "Money") -> bool:
        return self.amount == other.amount and self.currency == other.currency
    
    def add(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise InvalidValueObjectException("Cannot add money with different currencies")
        return Money(self.amount + other.amount, self.currency)
    
    def subtract(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise InvalidValueObjectException("Cannot subtract money with different currencies")
        return Money(self.amount - other.amount, self.currency)
