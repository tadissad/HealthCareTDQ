"""
Auth Service - Domain Layer - Value Objects
JWT authentication and authorization system
"""

from shared_ddd.base import ValueObject
import re


class UserId(ValueObject):
    """User identifier"""
    
    def __init__(self, value: str):
        if not value or len(value) < 1:
            raise ValueError("UserId cannot be empty")
        self.value = str(value)
    
    def __eq__(self, other):
        return isinstance(other, UserId) and self.value == other.value
    
    def __hash__(self):
        return hash(self.value)


class Email(ValueObject):
    """Email address with validation"""
    
    EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    def __init__(self, value: str):
        if not re.match(self.EMAIL_PATTERN, value):
            raise ValueError(f"Invalid email format: {value}")
        self.value = value.lower()
    
    def __eq__(self, other):
        return isinstance(other, Email) and self.value == other.value
    
    def __hash__(self):
        return hash(self.value)


class CredentialHash(ValueObject):
    """Hashed password credential"""
    
    def __init__(self, hash_value: str):
        if not hash_value or len(hash_value) < 10:
            raise ValueError("Invalid credential hash")
        self.value = hash_value
    
    def __eq__(self, other):
        return isinstance(other, CredentialHash) and self.value == other.value
    
    def __hash__(self):
        return hash(self.value)


class Token(ValueObject):
    """JWT token value object"""
    
    def __init__(self, value: str, token_type: str = "Bearer"):
        if not value or len(value) < 20:
            raise ValueError("Invalid token")
        self.value = value
        self.token_type = token_type
    
    def __eq__(self, other):
        return isinstance(other, Token) and self.value == other.value
    
    def __hash__(self):
        return hash(self.value)


class Role(ValueObject):
    """User role"""
    
    VALID_ROLES = [
        'ADMIN',
        'CLINICIAN',
        'PHARMACIST',
        'PATIENT',
        'NURSE',
        'MANAGER',
        'STAFF'
    ]
    
    def __init__(self, name: str):
        if name not in self.VALID_ROLES:
            raise ValueError(f"Invalid role: {name}. Must be one of {self.VALID_ROLES}")
        self.name = name
    
    def __eq__(self, other):
        return isinstance(other, Role) and self.name == other.name
    
    def __hash__(self):
        return hash(self.name)


class Permission(ValueObject):
    """Permission granted to role"""
    
    def __init__(self, resource: str, action: str):
        """
        Example: Permission('prescriptions', 'write')
        """
        if not resource or not action:
            raise ValueError("Resource and action must be provided")
        self.resource = resource
        self.action = action
    
    def __eq__(self, other):
        return (isinstance(other, Permission) and 
                self.resource == other.resource and 
                self.action == other.action)
    
    def __hash__(self):
        return hash((self.resource, self.action))


class JWTClaims(ValueObject):
    """JWT token claims"""
    
    def __init__(self, user_id: str, email: str, roles: list, 
                 exp: int, iat: int):
        self.user_id = user_id
        self.email = email
        self.roles = roles  # List of role names
        self.exp = exp  # Expiration timestamp
        self.iat = iat  # Issued at timestamp
    
    def is_expired(self, current_timestamp: int) -> bool:
        """Check if token is expired"""
        return current_timestamp > self.exp
    
    def has_role(self, role_name: str) -> bool:
        """Check if user has specific role"""
        return role_name in self.roles
    
    def __eq__(self, other):
        return (isinstance(other, JWTClaims) and 
                self.user_id == other.user_id and 
                self.email == other.email)
    
    def __hash__(self):
        return hash(self.user_id)


class AuthenticationContext(ValueObject):
    """Context for authentication operation"""
    
    def __init__(self, email: str, password: str, ip_address: str = None):
        self.email = email
        self.password = password
        self.ip_address = ip_address
    
    def __eq__(self, other):
        return isinstance(other, AuthenticationContext) and self.email == other.email


class AuthorizationContext(ValueObject):
    """Context for authorization check"""
    
    def __init__(self, user_id: str, resource: str, action: str):
        self.user_id = user_id
        self.resource = resource
        self.action = action
    
    def __eq__(self, other):
        return (isinstance(other, AuthorizationContext) and 
                self.user_id == other.user_id and 
                self.resource == other.resource and 
                self.action == other.action)
