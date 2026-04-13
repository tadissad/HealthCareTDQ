"""
Auth Service - Domain Layer - Repositories
Repository interfaces for Auth aggregates
"""

from typing import Optional, List
from shared_ddd.base import IRepository
from auth_service.domain.entities import User, RolePermissionMap
from auth_service.domain.value_objects import UserId, Email, Role, Permission


class IUserRepository(IRepository):
    """Repository interface for User aggregate"""
    
    def save(self, user: User) -> None:
        """Save user to persistence"""
        pass
    
    def get_by_id(self, user_id: UserId) -> Optional[User]:
        """Get user by ID"""
        pass
    
    def get_by_email(self, email: Email) -> Optional[User]:
        """Get user by email"""
        pass
    
    def get_by_email_string(self, email: str) -> Optional[User]:
        """Get user by email string"""
        pass
    
    def get_active_users(self, limit: int = 100) -> List[User]:
        """Get all active users"""
        pass
    
    def get_locked_users(self) -> List[User]:
        """Get all locked user accounts"""
        pass
    
    def search_by_email(self, email_query: str) -> List[User]:
        """Search users by email pattern"""
        pass


class IRolePermissionRepository(IRepository):
    """Repository interface for Role permissions"""
    
    def save(self, role_map: RolePermissionMap) -> None:
        """Save role permission mapping"""
        pass
    
    def get_by_role(self, role: Role) -> Optional[RolePermissionMap]:
        """Get permissions for role"""
        pass
    
    def get_all_permissions(self) -> List[Permission]:
        """Get all available permissions"""
        pass
    
    def check_permission(self, role: Role, resource: str, action: str) -> bool:
        """Check if role has permission"""
        pass


class ITokenRepository(IRepository):
    """Repository for token blacklist/validation"""
    
    def save_token(self, user_id: str, token: str, expires_at: int) -> None:
        """Save token metadata"""
        pass
    
    def revoke_token(self, token: str) -> None:
        """Revoke token (add to blacklist)"""
        pass
    
    def is_token_revoked(self, token: str) -> bool:
        """Check if token is revoked"""
        pass
    
    def get_active_tokens_for_user(self, user_id: str) -> List[str]:
        """Get all active tokens for user"""
        pass
    
    def cleanup_expired_tokens(self) -> int:
        """Delete expired tokens, return count deleted"""
        pass
