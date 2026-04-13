"""
Auth Service - Domain Layer - Entities
User, Role, and Permission aggregates
"""

from datetime import datetime, timedelta
from typing import List, Optional, Set
from shared_ddd.base import Aggregate, Entity
from auth_service.domain.value_objects import (
    UserId, Email, CredentialHash, Token, Role, Permission, JWTClaims,
    AuthenticationContext, AuthorizationContext
)
from auth_service.domain.events import (
    UserRegistered, UserLoggedIn, UserLoggedOut, RoleAssigned, RoleRevoked,
    TokenGenerated, TokenValidated, TokenInvalid, AuthorizationGranted,
    AuthorizationDenied, PasswordChanged, FailedLoginAttempt, AccountLocked
)
import time


class User(Aggregate):
    """User aggregate root"""
    
    def __init__(self, user_id: UserId, email: Email, credential_hash: CredentialHash):
        super().__init__()
        self.user_id = user_id
        self.email = email
        self.credential_hash = credential_hash
        self.roles: Set[Role] = set()
        self.is_active = True
        self.is_locked = False
        self.failed_login_attempts = 0
        self.last_login_at = None
        self.created_at = int(time.time())
        
        # Publish event
        self.domain_events.append(UserRegistered(
            user_id=user_id.value,
            email=email.value,
            registration_timestamp=self.created_at
        ))
    
    def add_role(self, role: Role, assigned_by: str = "SYSTEM"):
        """Add role to user"""
        if role not in self.roles:
            self.roles.add(role)
            self.domain_events.append(RoleAssigned(
                user_id=self.user_id.value,
                role=role.name,
                assigned_by=assigned_by,
                timestamp=int(time.time())
            ))
    
    def remove_role(self, role: Role, revoked_by: str = "SYSTEM"):
        """Remove role from user"""
        if role in self.roles:
            self.roles.remove(role)
            self.domain_events.append(RoleRevoked(
                user_id=self.user_id.value,
                role=role.name,
                revoked_by=revoked_by,
                timestamp=int(time.time())
            ))
    
    def has_role(self, role: Role) -> bool:
        """Check if user has role"""
        return role in self.roles
    
    def get_role_names(self) -> List[str]:
        """Get all role names"""
        return [role.name for role in self.roles]
    
    def authenticate(self, password: str, ip_address: str = None) -> bool:
        """Authenticate user password"""
        if self.is_locked:
            self.domain_events.append(FailedLoginAttempt(
                email=self.email.value,
                ip_address=ip_address or "unknown",
                reason="Account locked",
                attempt_at=int(time.time())
            ))
            return False
        
        # In real implementation, use bcrypt to compare
        # This is simplified version
        if password == self.credential_hash.value:
            self.failed_login_attempts = 0
            self.last_login_at = int(time.time())
            self.domain_events.append(UserLoggedIn(
                user_id=self.user_id.value,
                email=self.email.value,
                ip_address=ip_address or "unknown",
                login_timestamp=self.last_login_at
            ))
            return True
        else:
            self.failed_login_attempts += 1
            if self.failed_login_attempts >= 5:
                self.is_locked = True
                unlock_at = int(time.time()) + (30 * 60)  # 30 minutes
                self.domain_events.append(AccountLocked(
                    user_id=self.user_id.value,
                    reason="Too many failed login attempts",
                    locked_at=int(time.time()),
                    unlock_at=unlock_at
                ))
            else:
                self.domain_events.append(FailedLoginAttempt(
                    email=self.email.value,
                    ip_address=ip_address or "unknown",
                    reason="Invalid password",
                    attempt_at=int(time.time())
                ))
            return False
    
    def change_password(self, new_credential_hash: CredentialHash, ip_address: str = None):
        """Change user password"""
        self.credential_hash = new_credential_hash
        self.domain_events.append(PasswordChanged(
            user_id=self.user_id.value,
            changed_at=int(time.time()),
            ip_address=ip_address or "unknown"
        ))
    
    def unlock_account(self):
        """Unlock locked account"""
        self.is_locked = False
        self.failed_login_attempts = 0
    
    def deactivate(self):
        """Deactivate user account"""
        self.is_active = False
    
    def activate(self):
        """Activate user account"""
        self.is_active = True


class RolePermissionMap(Aggregate):
    """Role to Permission mapping aggregate"""
    
    def __init__(self, role: Role):
        super().__init__()
        self.role = role
        self.permissions: Set[Permission] = set()
    
    def add_permission(self, permission: Permission):
        """Add permission to role"""
        if permission not in self.permissions:
            self.permissions.add(permission)
            from auth_service.domain.events import PermissionAdded
            self.domain_events.append(PermissionAdded(
                role=self.role.name,
                resource=permission.resource,
                action=permission.action,
                added_at=int(time.time())
            ))
    
    def remove_permission(self, permission: Permission):
        """Remove permission from role"""
        if permission in self.permissions:
            self.permissions.remove(permission)
            from auth_service.domain.events import PermissionRemoved
            self.domain_events.append(PermissionRemoved(
                role=self.role.name,
                resource=permission.resource,
                action=permission.action,
                removed_at=int(time.time())
            ))
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if role has permission"""
        return permission in self.permissions
    
    def check_access(self, resource: str, action: str) -> bool:
        """Check if specific access is granted"""
        return Permission(resource, action) in self.permissions


class TokenBundle(Entity):
    """Bundle of tokens for user"""
    
    def __init__(self, user_id: UserId, access_token: Token, 
                 refresh_token: Token, expires_in: int):
        self.user_id = user_id
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expires_in = expires_in
        self.issued_at = int(time.time())
        self.expires_at = self.issued_at + expires_in
    
    def is_expired(self) -> bool:
        """Check if token bundle is expired"""
        return int(time.time()) > self.expires_at
    
    def is_refresh_valid(self) -> bool:
        """Check if refresh token is still valid (usually 7 days)"""
        refresh_expiry = self.issued_at + (7 * 24 * 60 * 60)  # 7 days
        return int(time.time()) <= refresh_expiry
