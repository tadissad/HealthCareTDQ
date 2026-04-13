"""
Auth Service - Domain Layer - Events
Authentication and authorization domain events
"""

from shared_ddd.base import DomainEvent
from dataclasses import dataclass


@dataclass
class UserRegistered(DomainEvent):
    """User registered event"""
    user_id: str
    email: str
    registration_timestamp: int
    event_type: str = "UserRegistered"


@dataclass
class UserLoggedIn(DomainEvent):
    """User logged in event"""
    user_id: str
    email: str
    ip_address: str
    login_timestamp: int
    event_type: str = "UserLoggedIn"


@dataclass
class UserLoggedOut(DomainEvent):
    """User logged out event"""
    user_id: str
    logout_timestamp: int
    event_type: str = "UserLoggedOut"


@dataclass
class RoleAssigned(DomainEvent):
    """Role assigned to user"""
    user_id: str
    role: str
    assigned_by: str
    timestamp: int
    event_type: str = "RoleAssigned"


@dataclass
class RoleRevoked(DomainEvent):
    """Role revoked from user"""
    user_id: str
    role: str
    revoked_by: str
    timestamp: int
    event_type: str = "RoleRevoked"


@dataclass
class TokenGenerated(DomainEvent):
    """JWT token generated"""
    user_id: str
    token_type: str
    expires_at: int
    generated_at: int
    event_type: str = "TokenGenerated"


@dataclass
class TokenValidated(DomainEvent):
    """Token validated successfully"""
    user_id: str
    validated_at: int
    event_type: str = "TokenValidated"


@dataclass
class TokenInvalid(DomainEvent):
    """Token validation failed"""
    reason: str
    attempted_at: int
    event_type: str = "TokenInvalid"


@dataclass
class AuthorizationGranted(DomainEvent):
    """Authorization check passed"""
    user_id: str
    resource: str
    action: str
    checked_at: int
    event_type: str = "AuthorizationGranted"


@dataclass
class AuthorizationDenied(DomainEvent):
    """Authorization check failed"""
    user_id: str
    resource: str
    action: str
    reason: str
    checked_at: int
    event_type: str = "AuthorizationDenied"


@dataclass
class PasswordChanged(DomainEvent):
    """User password changed"""
    user_id: str
    changed_at: int
    ip_address: str
    event_type: str = "PasswordChanged"


@dataclass
class PermissionAdded(DomainEvent):
    """Permission added to role"""
    role: str
    resource: str
    action: str
    added_at: int
    event_type: str = "PermissionAdded"


@dataclass
class PermissionRemoved(DomainEvent):
    """Permission removed from role"""
    role: str
    resource: str
    action: str
    removed_at: int
    event_type: str = "PermissionRemoved"


@dataclass
class FailedLoginAttempt(DomainEvent):
    """Failed login attempt logged"""
    email: str
    ip_address: str
    reason: str
    attempt_at: int
    event_type: str = "FailedLoginAttempt"


@dataclass
class AccountLocked(DomainEvent):
    """Account locked after failed attempts"""
    user_id: str
    reason: str
    locked_at: int
    unlock_at: int
    event_type: str = "AccountLocked"
