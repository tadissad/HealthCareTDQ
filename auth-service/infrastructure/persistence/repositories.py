"""
Auth Service - Infrastructure Layer - Repositories
Repository implementations for User, Role, Token persistence
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List
from auth_service.domain.repositories import IUserRepository, IRolePermissionRepository, ITokenRepository
from auth_service.domain.entities import User, RolePermissionMap
from auth_service.domain.value_objects import UserId, Email, CredentialHash, Role, Permission
from auth_service.infrastructure.persistence.models import (
    UserModel, UserRoleModel, RoleModel, PermissionModel, RolePermissionModel,
    TokenModel, AuthLogModel
)
from shared_ddd.event_bus import EventBusFactory

logger = logging.getLogger(__name__)


class UserRepositoryImpl(IUserRepository):
    """Repository implementation for User aggregate"""
    
    def save(self, user: User) -> None:
        """Save user to database"""
        try:
            user_model, created = UserModel.objects.update_or_create(
                user_id=user.user_id.value,
                defaults={
                    'email': user.email.value,
                    'password_hash': user.credential_hash.value,
                    'is_active': user.is_active,
                    'is_locked': user.is_locked,
                    'failed_login_attempts': user.failed_login_attempts,
                }
            )
            
            # Update roles
            UserRoleModel.objects.filter(user=user_model).delete()
            for role in user.roles:
                UserRoleModel.objects.create(
                    user=user_model,
                    role=role.name
                )
            
            # Publish events
            self._publish_events(user)
            
            logger.info(f"User saved: {user.email.value}")
        
        except Exception as e:
            logger.error(f"Error saving user: {e}")
            raise
    
    def get_by_id(self, user_id: UserId) -> Optional[User]:
        """Get user by ID"""
        try:
            model = UserModel.objects.get(user_id=user_id.value)
            return self._model_to_entity(model)
        except UserModel.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error retrieving user by ID: {e}")
            return None
    
    def get_by_email(self, email: Email) -> Optional[User]:
        """Get user by email value object"""
        try:
            model = UserModel.objects.get(email=email.value)
            return self._model_to_entity(model)
        except UserModel.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error retrieving user by email: {e}")
            return None
    
    def get_by_email_string(self, email: str) -> Optional[User]:
        """Get user by email string"""
        try:
            model = UserModel.objects.get(email=email)
            return self._model_to_entity(model)
        except UserModel.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error retrieving user by email string: {e}")
            return None
    
    def get_active_users(self, limit: int = 100) -> List[User]:
        """Get all active users"""
        try:
            models = UserModel.objects.filter(is_active=True).order_by('-created_at')[:limit]
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            logger.error(f"Error retrieving active users: {e}")
            return []
    
    def get_locked_users(self) -> List[User]:
        """Get all locked users"""
        try:
            models = UserModel.objects.filter(is_locked=True)
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            logger.error(f"Error retrieving locked users: {e}")
            return []
    
    def search_by_email(self, email_query: str) -> List[User]:
        """Search users by email pattern"""
        try:
            models = UserModel.objects.filter(email__icontains=email_query)[:50]
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            logger.error(f"Error searching users: {e}")
            return []
    
    def _model_to_entity(self, model: UserModel) -> User:
        """Convert ORM model to domain entity"""
        user = User(
            user_id=UserId(model.user_id),
            email=Email(model.email),
            credential_hash=CredentialHash(model.password_hash)
        )
        
        user.is_active = model.is_active
        user.is_locked = model.is_locked
        user.failed_login_attempts = model.failed_login_attempts
        user.last_login_at = model.last_login_at.timestamp() if model.last_login_at else None
        
        # Load roles
        role_models = model.user_roles.all()
        for role_model in role_models:
            user.roles.add(Role(role_model.role))
        
        return user
    
    def _publish_events(self, user: User):
        """Publish domain events"""
        try:
            publisher = EventBusFactory.get_publisher()
            for event in user.domain_events:
                publisher.publish(event)
            user.domain_events.clear()
        except Exception as e:
            logger.warning(f"Could not publish user events: {e}")


class RolePermissionRepositoryImpl(IRolePermissionRepository):
    """Repository implementation for Role permissions"""
    
    def save(self, role_map: RolePermissionMap) -> None:
        """Save role permission mapping"""
        try:
            role_model, _ = RoleModel.objects.get_or_create(name=role_map.role.name)
            
            # Clear existing permissions
            RolePermissionModel.objects.filter(role=role_model).delete()
            
            # Add new permissions
            for permission in role_map.permissions:
                perm_model, _ = PermissionModel.objects.get_or_create(
                    resource=permission.resource,
                    action=permission.action
                )
                RolePermissionModel.objects.create(
                    role=role_model,
                    permission=perm_model
                )
            
            # Publish events
            self._publish_events(role_map)
            
            logger.info(f"Role permissions saved: {role_map.role.name}")
        
        except Exception as e:
            logger.error(f"Error saving role permissions: {e}")
            raise
    
    def get_by_role(self, role: Role) -> Optional[RolePermissionMap]:
        """Get permissions for role"""
        try:
            role_model = RoleModel.objects.get(name=role.name)
            
            role_map = RolePermissionMap(role)
            
            perm_models = RolePermissionModel.objects.filter(role=role_model)
            for perm_model in perm_models:
                perm = Permission(
                    perm_model.permission.resource,
                    perm_model.permission.action
                )
                role_map.permissions.add(perm)
            
            return role_map
        
        except RoleModel.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error retrieving role permissions: {e}")
            return None
    
    def get_all_permissions(self) -> List[Permission]:
        """Get all available permissions"""
        try:
            perm_models = PermissionModel.objects.all()
            return [Permission(p.resource, p.action) for p in perm_models]
        except Exception as e:
            logger.error(f"Error retrieving all permissions: {e}")
            return []
    
    def check_permission(self, role: Role, resource: str, action: str) -> bool:
        """Check if role has permission"""
        try:
            return RolePermissionModel.objects.filter(
                role__name=role.name,
                permission__resource=resource,
                permission__action=action
            ).exists()
        except Exception as e:
            logger.error(f"Error checking permission: {e}")
            return False
    
    def _publish_events(self, role_map: RolePermissionMap):
        """Publish domain events"""
        try:
            publisher = EventBusFactory.get_publisher()
            for event in role_map.domain_events:
                publisher.publish(event)
            role_map.domain_events.clear()
        except Exception as e:
            logger.warning(f"Could not publish role permission events: {e}")


class TokenRepositoryImpl(ITokenRepository):
    """Repository for token management"""
    
    def save_token(self, user_id: str, token: str, expires_at: int) -> None:
        """Save token metadata"""
        try:
            user_model = UserModel.objects.get(user_id=user_id)
            
            TokenModel.objects.create(
                user=user_model,
                token_hash=token,
                expires_at=datetime.fromtimestamp(expires_at)
            )
            
            logger.info(f"Token saved for user: {user_id}")
        
        except Exception as e:
            logger.error(f"Error saving token: {e}")
    
    def revoke_token(self, token: str) -> None:
        """Revoke token (add to blacklist)"""
        try:
            token_model = TokenModel.objects.get(token_hash=token)
            token_model.revoked_at = datetime.now()
            token_model.save()
            
            logger.info("Token revoked")
        
        except TokenModel.DoesNotExist:
            pass
        except Exception as e:
            logger.error(f"Error revoking token: {e}")
    
    def is_token_revoked(self, token: str) -> bool:
        """Check if token is revoked"""
        try:
            token_model = TokenModel.objects.get(token_hash=token)
            return token_model.revoked_at is not None
        except TokenModel.DoesNotExist:
            return False
        except Exception as e:
            logger.error(f"Error checking token revocation: {e}")
            return False
    
    def get_active_tokens_for_user(self, user_id: str) -> List[str]:
        """Get all active tokens for user"""
        try:
            tokens = TokenModel.objects.filter(
                user__user_id=user_id,
                revoked_at__isnull=True,
                expires_at__gt=datetime.now()
            )
            return [t.token_hash for t in tokens]
        except Exception as e:
            logger.error(f"Error getting active tokens: {e}")
            return []
    
    def cleanup_expired_tokens(self) -> int:
        """Delete expired tokens, return count deleted"""
        try:
            deleted_count, _ = TokenModel.objects.filter(
                expires_at__lt=datetime.now()
            ).delete()
            logger.info(f"Cleaned up {deleted_count} expired tokens")
            return deleted_count
        except Exception as e:
            logger.error(f"Error cleaning up tokens: {e}")
            return 0
