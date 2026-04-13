"""
Auth Service - Application Layer - Commands and Queries
CQRS patterns for authentication operations
"""

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime


# ============ COMMANDS ============

@dataclass
class RegisterUserCommand:
    """Register new user"""
    email: str
    password: str


@dataclass
class LoginUserCommand:
    """User login"""
    email: str
    password: str
    ip_address: Optional[str] = None


@dataclass
class LogoutUserCommand:
    """User logout"""
    user_id: str
    token: str


@dataclass
class AssignRoleCommand:
    """Assign role to user"""
    user_id: str
    role: str
    assigned_by: str = "SYSTEM"


@dataclass
class RevokeRoleCommand:
    """Revoke role from user"""
    user_id: str
    role: str
    revoked_by: str = "SYSTEM"


@dataclass
class ChangePasswordCommand:
    """Change user password"""
    user_id: str
    old_password: str
    new_password: str
    ip_address: Optional[str] = None


@dataclass
class ValidateTokenCommand:
    """Validate JWT token"""
    token: str


@dataclass
class RefreshTokenCommand:
    """Refresh access token"""
    refresh_token: str
    user_id: str


@dataclass
class GrantPermissionCommand:
    """Grant permission to role"""
    role: str
    resource: str
    action: str


@dataclass
class RevokePermissionCommand:
    """Revoke permission from role"""
    role: str
    resource: str
    action: str


@dataclass
class LockAccountCommand:
    """Lock user account"""
    user_id: str
    reason: str


@dataclass
class UnlockAccountCommand:
    """Unlock user account"""
    user_id: str


# ============ QUERIES ============

@dataclass
class GetUserByIdQuery:
    """Get user by ID"""
    user_id: str


@dataclass
class GetUserByEmailQuery:
    """Get user by email"""
    email: str


@dataclass
class GetUserRolesQuery:
    """Get user's roles"""
    user_id: str


@dataclass
class CheckAccessQuery:
    """Check if user has access"""
    user_id: str
    resource: str
    action: str


@dataclass
class ValidateAccessTokenQuery:
    """Validate and get token claims"""
    token: str


@dataclass
class GetRolePermissionsQuery:
    """Get all permissions for role"""
    role: str


@dataclass
class ListUsersQuery:
    """List users with filters"""
    active_only: bool = True
    limit: int = 50


@dataclass
class ListDataAccessLogsQuery:
    """List authentication/authorization logs"""
    user_id: Optional[str] = None
    limit: int = 100


# ============ COMMAND RESULTS ============

@dataclass
class RegisterUserResult:
    """Result of user registration"""
    success: bool
    user_id: Optional[str] = None
    message: str = ""


@dataclass
class LoginUserResult:
    """Result of user login"""
    success: bool
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_in: int = 0
    user_id: Optional[str] = None
    message: str = ""


@dataclass
class TokenValidationResult:
    """Result of token validation"""
    valid: bool
    user_id: Optional[str] = None
    email: Optional[str] = None
    roles: List[str] = None
    expires_at: Optional[int] = None
    message: str = ""


@dataclass
class AccessCheckResult:
    """Result of access check"""
    granted: bool
    reason: str = ""


@dataclass
class PermissionOperationResult:
    """Result of permission grant/revoke"""
    success: bool
    message: str = ""


# ============ QUERY RESPONSES ============

@dataclass
class UserDTO:
    """User data transfer object"""
    user_id: str
    email: str
    roles: List[str]
    is_active: bool
    is_locked: bool
    created_at: str
    last_login_at: Optional[str] = None


@dataclass
class RolePermissionDTO:
    """Role with permissions"""
    role: str
    permissions: List[dict]  # [{"resource": "...", "action": "..."}]


@dataclass
class AuthLogDTO:
    """Authentication log entry"""
    event_type: str  # LOGIN, LOGOUT, FAILED_LOGIN, etc
    user_id: Optional[str] = None
    email: Optional[str] = None
    ip_address: Optional[str] = None
    timestamp: Optional[str] = None
    details: Optional[str] = None
