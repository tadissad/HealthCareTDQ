"""
Auth Service - Application Layer - Handlers
Command and Query handlers implementing use cases
"""

import logging
from typing import Optional
from auth_service.application.commands_queries import (
    RegisterUserCommand, LoginUserCommand, LogoutUserCommand,
    AssignRoleCommand, RevokeRoleCommand, ChangePasswordCommand,
    ValidateTokenCommand, RefreshTokenCommand, GrantPermissionCommand,
    RevokePermissionCommand, LockAccountCommand, UnlockAccountCommand,
    RegisterUserResult, LoginUserResult, TokenValidationResult,
    AccessCheckResult, PermissionOperationResult,
    GetUserByIdQuery, GetUserByEmailQuery, GetUserRolesQuery,
    CheckAccessQuery, ValidateAccessTokenQuery, GetRolePermissionsQuery,
    ListUsersQuery, UserDTO, RolePermissionDTO
)
from auth_service.domain.value_objects import Role, Email
from shared_ddd.event_bus import EventBusFactory

logger = logging.getLogger(__name__)


class RegisterUserHandler:
    """Handle user registration"""
    
    def __init__(self, user_repo, auth_service):
        self.user_repo = user_repo
        self.auth_service = auth_service
    
    def handle(self, command: RegisterUserCommand) -> RegisterUserResult:
        """Register new user"""
        try:
            success, user = self.auth_service.register_user(
                email=command.email,
                password=command.password
            )
            
            if success:
                self._publish_events(user)
                return RegisterUserResult(
                    success=True,
                    user_id=user.user_id.value,
                    message="User registered successfully"
                )
            else:
                return RegisterUserResult(
                    success=False,
                    message="User registration failed"
                )
        except Exception as e:
            logger.error(f"Registration handler error: {e}")
            return RegisterUserResult(success=False, message=str(e))
    
    def _publish_events(self, user):
        """Publish user events"""
        try:
            publisher = EventBusFactory.get_publisher()
            for event in user.domain_events:
                publisher.publish(event)
            user.domain_events.clear()
        except:
            logger.warning("Could not publish registration events")


class LoginUserHandler:
    """Handle user login"""
    
    def __init__(self, user_repo, auth_service, token_service):
        self.user_repo = user_repo
        self.auth_service = auth_service
        self.token_service = token_service
    
    def handle(self, command: LoginUserCommand) -> LoginUserResult:
        """Handle login"""
        try:
            success, user = self.auth_service.authenticate_user(
                email=command.email,
                password=command.password,
                ip_address=command.ip_address
            )
            
            if not success:
                return LoginUserResult(
                    success=False,
                    message="Invalid email or password"
                )
            
            # Generate tokens
            token_bundle = self.token_service.generate_tokens(user)
            if not token_bundle:
                return LoginUserResult(
                    success=False,
                    message="Token generation failed"
                )
            
            # Persist user state
            self.user_repo.save(user)
            
            # Publish events
            self._publish_events(user)
            
            return LoginUserResult(
                success=True,
                access_token=token_bundle.access_token.value,
                refresh_token=token_bundle.refresh_token.value,
                expires_in=token_bundle.expires_in,
                user_id=user.user_id.value,
                message="Login successful"
            )
        
        except Exception as e:
            logger.error(f"Login handler error: {e}")
            return LoginUserResult(success=False, message=str(e))
    
    def _publish_events(self, user):
        """Publish user events"""
        try:
            publisher = EventBusFactory.get_publisher()
            for event in user.domain_events:
                publisher.publish(event)
            user.domain_events.clear()
        except:
            logger.warning("Could not publish login events")


class LogoutUserHandler:
    """Handle user logout"""
    
    def __init__(self, token_service):
        self.token_service = token_service
    
    def handle(self, command: LogoutUserCommand) -> bool:
        """Handle logout"""
        try:
            self.token_service.revoke_token(command.token)
            logger.info(f"User logged out: {command.user_id}")
            return True
        except Exception as e:
            logger.error(f"Logout handler error: {e}")
            return False


class AssignRoleHandler:
    """Handle role assignment"""
    
    def __init__(self, user_repo):
        self.user_repo = user_repo
    
    def handle(self, command: AssignRoleCommand) -> PermissionOperationResult:
        """Assign role to user"""
        try:
            from auth_service.domain.value_objects import UserId
            user = self.user_repo.get_by_id(UserId(command.user_id))
            
            if not user:
                return PermissionOperationResult(
                    success=False,
                    message="User not found"
                )
            
            role = Role(command.role)
            user.add_role(role, assigned_by=command.assigned_by)
            self.user_repo.save(user)
            
            self._publish_events(user)
            
            return PermissionOperationResult(
                success=True,
                message=f"Role {command.role} assigned"
            )
        
        except Exception as e:
            logger.error(f"Assign role error: {e}")
            return PermissionOperationResult(success=False, message=str(e))
    
    def _publish_events(self, user):
        try:
            publisher = EventBusFactory.get_publisher()
            for event in user.domain_events:
                publisher.publish(event)
            user.domain_events.clear()
        except:
            pass


class ValidateTokenHandler:
    """Handle token validation"""
    
    def __init__(self, token_service):
        self.token_service = token_service
    
    def handle(self, command: ValidateTokenCommand) -> TokenValidationResult:
        """Validate token"""
        try:
            valid, claims = self.token_service.validate_token(command.token)
            
            if not valid:
                return TokenValidationResult(
                    valid=False,
                    message="Token is invalid or expired"
                )
            
            return TokenValidationResult(
                valid=True,
                user_id=claims.user_id,
                email=claims.email,
                roles=claims.roles,
                expires_at=claims.exp,
                message="Token is valid"
            )
        
        except Exception as e:
            logger.error(f"Token validation handler error: {e}")
            return TokenValidationResult(valid=False, message=str(e))


class CheckAccessHandler:
    """Handle access check"""
    
    def __init__(self, user_repo, authz_service):
        self.user_repo = user_repo
        self.authz_service = authz_service
    
    def handle(self, command) -> AccessCheckResult:
        """Check if user has access"""
        try:
            from auth_service.domain.value_objects import UserId
            user = self.user_repo.get_by_id(UserId(command.user_id))
            
            if not user:
                return AccessCheckResult(
                    granted=False,
                    reason="User not found"
                )
            
            granted, reason = self.authz_service.check_access(
                user,
                command.resource,
                command.action
            )
            
            return AccessCheckResult(granted=granted, reason=reason)
        
        except Exception as e:
            logger.error(f"Access check handler error: {e}")
            return AccessCheckResult(granted=False, reason=str(e))


# ============ QUERY HANDLERS ============

class GetUserByIdHandler:
    """Get user by ID"""
    
    def __init__(self, user_repo):
        self.user_repo = user_repo
    
    def handle(self, query: GetUserByIdQuery) -> Optional[UserDTO]:
        """Get user"""
        try:
            from auth_service.domain.value_objects import UserId
            user = self.user_repo.get_by_id(UserId(query.user_id))
            
            if not user:
                return None
            
            return UserDTO(
                user_id=user.user_id.value,
                email=user.email.value,
                roles=user.get_role_names(),
                is_active=user.is_active,
                is_locked=user.is_locked,
                created_at=str(user.created_at),
                last_login_at=str(user.last_login_at) if user.last_login_at else None
            )
        
        except Exception as e:
            logger.error(f"Get user handler error: {e}")
            return None


class GetUserByEmailHandler:
    """Get user by email"""
    
    def __init__(self, user_repo):
        self.user_repo = user_repo
    
    def handle(self, query: GetUserByEmailQuery) -> Optional[UserDTO]:
        """Get user by email"""
        try:
            user = self.user_repo.get_by_email_string(query.email)
            
            if not user:
                return None
            
            return UserDTO(
                user_id=user.user_id.value,
                email=user.email.value,
                roles=user.get_role_names(),
                is_active=user.is_active,
                is_locked=user.is_locked,
                created_at=str(user.created_at),
                last_login_at=str(user.last_login_at) if user.last_login_at else None
            )
        
        except Exception as e:
            logger.error(f"Get user by email handler error: {e}")
            return None


class GetUserRolesHandler:
    """Get user roles"""
    
    def __init__(self, user_repo):
        self.user_repo = user_repo
    
    def handle(self, query: GetUserRolesQuery) -> list:
        """Get user roles"""
        try:
            from auth_service.domain.value_objects import UserId
            user = self.user_repo.get_by_id(UserId(query.user_id))
            
            if not user:
                return []
            
            return user.get_role_names()
        
        except Exception as e:
            logger.error(f"Get roles handler error: {e}")
            return []
