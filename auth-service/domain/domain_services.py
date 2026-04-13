"""
Auth Service - Domain Layer - Domain Services
Authentication, Authorization, and Token management services
"""

import time
import logging
from typing import Optional, Tuple
from shared_ddd.base import DomainService
from auth_service.domain.entities import User, RolePermissionMap, TokenBundle
from auth_service.domain.value_objects import (
    UserId, Email, CredentialHash, Token, Role, Permission, JWTClaims,
    AuthenticationContext, AuthorizationContext
)
from auth_service.domain.events import TokenGenerated, TokenValidated, TokenInvalid, AuthorizationGranted, AuthorizationDenied

logger = logging.getLogger(__name__)


class AuthenticationService(DomainService):
    """Handle authentication operations"""
    
    def __init__(self, user_repository, token_repository):
        self.user_repository = user_repository
        self.token_repository = token_repository
    
    def authenticate_user(self, email: str, password: str, 
                         ip_address: str = None) -> Tuple[bool, Optional[User]]:
        """
        Authenticate user with email and password
        Returns: (success: bool, user: Optional[User])
        """
        try:
            user = self.user_repository.get_by_email_string(email)
            
            if not user:
                logger.warning(f"Authentication failed: user not found for {email}")
                return False, None
            
            if not user.is_active:
                logger.warning(f"Authentication failed: user inactive {email}")
                return False, None
            
            if user.authenticate(password, ip_address):
                logger.info(f"User authenticated: {email}")
                return True, user
            else:
                logger.warning(f"Authentication failed: invalid password for {email}")
                return False, user
        
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False, None
    
    def register_user(self, email: str, password: str) -> Tuple[bool, Optional[User]]:
        """
        Register new user
        Returns: (success: bool, user: Optional[User])
        """
        try:
            # Check if user exists
            existing = self.user_repository.get_by_email_string(email)
            if existing:
                logger.warning(f"Registration failed: user already exists {email}")
                return False, None
            
            # Create new user
            user_id = UserId(f"user_{int(time.time() * 1000)}")
            email_vo = Email(email)
            
            # In real implementation, use bcrypt
            cred_hash = CredentialHash(password)
            
            user = User(user_id, email_vo, cred_hash)
            
            # Set default role
            user.add_role(Role('PATIENT'), assigned_by='SYSTEM')
            
            self.user_repository.save(user)
            logger.info(f"User registered: {email}")
            return True, user
        
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return False, None


class AuthorizationService(DomainService):
    """Handle authorization operations"""
    
    def __init__(self, role_permission_repository):
        self.role_permission_repository = role_permission_repository
    
    def check_access(self, user: User, resource: str, action: str) -> Tuple[bool, str]:
        """
        Check if user has access to resource
        Returns: (authorized: bool, reason: str)
        """
        try:
            if not user.is_active:
                return False, "User account is inactive"
            
            for role in user.roles:
                role_map = self.role_permission_repository.get_by_role(role)
                if role_map and role_map.check_access(resource, action):
                    return True, "Access granted"
            
            return False, f"User lacks permission for {resource}:{action}"
        
        except Exception as e:
            logger.error(f"Authorization check error: {e}")
            return False, f"Authorization check failed: {str(e)}"
    
    def grant_role_permission(self, role: Role, resource: str, action: str) -> bool:
        """Grant permission to role"""
        try:
            permission = Permission(resource, action)
            role_map = self.role_permission_repository.get_by_role(role)
            
            if not role_map:
                role_map = RolePermissionMap(role)
            
            role_map.add_permission(permission)
            self.role_permission_repository.save(role_map)
            logger.info(f"Permission granted: {role.name} -> {resource}:{action}")
            return True
        
        except Exception as e:
            logger.error(f"Grant permission error: {e}")
            return False
    
    def revoke_role_permission(self, role: Role, resource: str, action: str) -> bool:
        """Revoke permission from role"""
        try:
            permission = Permission(resource, action)
            role_map = self.role_permission_repository.get_by_role(role)
            
            if role_map:
                role_map.remove_permission(permission)
                self.role_permission_repository.save(role_map)
                logger.info(f"Permission revoked: {role.name} -X {resource}:{action}")
            
            return True
        
        except Exception as e:
            logger.error(f"Revoke permission error: {e}")
            return False


class TokenManagementService(DomainService):
    """Handle JWT token generation and validation"""
    
    def __init__(self, token_repository, secret_key: str = "your-secret-key"):
        self.token_repository = token_repository
        self.secret_key = secret_key
        self.access_token_expiry = 15 * 60  # 15 minutes
        self.refresh_token_expiry = 7 * 24 * 60 * 60  # 7 days
    
    def generate_tokens(self, user: User) -> Optional[TokenBundle]:
        """
        Generate access and refresh tokens for user
        Returns: TokenBundle or None
        """
        try:
            issued_at = int(time.time())
            access_expires = issued_at + self.access_token_expiry
            
            # Simplified token generation (real implementation uses JWT library)
            access_token_value = self._create_jwt_token(
                user_id=user.user_id.value,
                email=user.email.value,
                roles=user.get_role_names(),
                exp=access_expires,
                iat=issued_at
            )
            
            refresh_token_value = self._create_jwt_token(
                user_id=user.user_id.value,
                email=user.email.value,
                roles=user.get_role_names(),
                exp=issued_at + self.refresh_token_expiry,
                iat=issued_at,
                token_type='refresh'
            )
            
            access_token = Token(access_token_value, token_type="Bearer")
            refresh_token = Token(refresh_token_value, token_type="Refresh")
            
            token_bundle = TokenBundle(
                user_id=user.user_id,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=self.access_token_expiry
            )
            
            # Save token metadata
            self.token_repository.save_token(
                user.user_id.value,
                access_token_value,
                access_expires
            )
            
            logger.info(f"Tokens generated for user: {user.email.value}")
            return token_bundle
        
        except Exception as e:
            logger.error(f"Token generation error: {e}")
            return None
    
    def validate_token(self, token_value: str) -> Tuple[bool, Optional[JWTClaims]]:
        """
        Validate JWT token
        Returns: (valid: bool, claims: Optional[JWTClaims])
        """
        try:
            if self.token_repository.is_token_revoked(token_value):
                return False, None
            
            # Simplified token validation (real implementation uses JWT.decode)
            claims = self._decode_jwt_token(token_value)
            
            if not claims:
                return False, None
            
            if claims.is_expired(int(time.time())):
                logger.warning(f"Token expired for user: {claims.user_id}")
                return False, None
            
            logger.info(f"Token validated for user: {claims.user_id}")
            return True, claims
        
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return False, None
    
    def revoke_token(self, token_value: str) -> bool:
        """Revoke token"""
        try:
            self.token_repository.revoke_token(token_value)
            logger.info("Token revoked")
            return True
        except Exception as e:
            logger.error(f"Token revocation error: {e}")
            return False
    
    def refresh_access_token(self, refresh_token: str, user: User) -> Optional[Token]:
        """Generate new access token using refresh token"""
        try:
            valid, claims = self.validate_token(refresh_token)
            
            if not valid:
                logger.warning("Refresh token invalid")
                return None
            
            issued_at = int(time.time())
            access_expires = issued_at + self.access_token_expiry
            
            access_token_value = self._create_jwt_token(
                user_id=user.user_id.value,
                email=user.email.value,
                roles=user.get_role_names(),
                exp=access_expires,
                iat=issued_at
            )
            
            self.token_repository.save_token(
                user.user_id.value,
                access_token_value,
                access_expires
            )
            
            logger.info(f"Access token refreshed for user: {user.email.value}")
            return Token(access_token_value, token_type="Bearer")
        
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return None
    
    def _create_jwt_token(self, user_id: str, email: str, roles: list,
                         exp: int, iat: int, token_type: str = 'access') -> str:
        """
        Create JWT token (simplified - real implementation uses PyJWT)
        """
        import json
        import base64
        
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "sub": user_id,
            "email": email,
            "roles": roles,
            "exp": exp,
            "iat": iat,
            "type": token_type
        }
        
        # Simplified encoding
        header_enc = base64.b64encode(json.dumps(header).encode()).decode()
        payload_enc = base64.b64encode(json.dumps(payload).encode()).decode()
        signature = base64.b64encode(
            f"{header_enc}.{payload_enc}.{self.secret_key}".encode()
        ).decode()
        
        return f"{header_enc}.{payload_enc}.{signature}"
    
    def _decode_jwt_token(self, token_value: str) -> Optional[JWTClaims]:
        """
        Decode JWT token (simplified - real implementation uses PyJWT)
        """
        import json
        import base64
        
        try:
            parts = token_value.split('.')
            if len(parts) != 3:
                return None
            
            payload_enc = parts[1]
            # Add padding if needed
            padding = 4 - len(payload_enc) % 4
            if padding != 4:
                payload_enc += '=' * padding
            
            payload_json = base64.b64decode(payload_enc).decode()
            payload = json.loads(payload_json)
            
            claims = JWTClaims(
                user_id=payload.get('sub'),
                email=payload.get('email'),
                roles=payload.get('roles', []),
                exp=payload.get('exp'),
                iat=payload.get('iat')
            )
            
            return claims
        
        except Exception as e:
            logger.error(f"Token decode error: {e}")
            return None
