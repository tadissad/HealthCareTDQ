"""
Auth Service - Interface Layer - HTTP Views
Django REST Framework views for authentication endpoints
"""

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.serializers import Serializer, CharField, IntegerField
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from auth_service.application.commands_queries import (
    RegisterUserCommand, LoginUserCommand, LogoutUserCommand,
    AssignRoleCommand, ValidateTokenCommand, CheckAccessQuery
)
from auth_service.application.handlers import (
    RegisterUserHandler, LoginUserHandler, LogoutUserHandler,
    AssignRoleHandler, ValidateTokenHandler, CheckAccessHandler,
    GetUserByIdHandler, GetUserByEmailHandler
)

logger = logging.getLogger(__name__)


# ============ REQUEST SERIALIZERS ============

class RegisterRequestSerializer(Serializer):
    email = CharField(max_length=255)
    password = CharField(max_length=255)


class LoginRequestSerializer(Serializer):
    email = CharField(max_length=255)
    password = CharField(max_length=255)
    ip_address = CharField(max_length=50, required=False, allow_blank=True)


class AssignRoleRequestSerializer(Serializer):
    user_id = CharField(max_length=50)
    role = CharField(max_length=50)
    assigned_by = CharField(max_length=50, required=False, default='SYSTEM')


class CheckAccessRequestSerializer(Serializer):
    user_id = CharField(max_length=50)
    resource = CharField(max_length=100)
    action = CharField(max_length=50)


# ============ API ENDPOINTS ============

class RegisterView(APIView):
    """POST /api/auth/register"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Register new user"""
        try:
            serializer = RegisterRequestSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            command = RegisterUserCommand(
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password']
            )
            
            # Get repositories from context (setup in __init__.py)
            from auth_service.infrastructure.persistence.repositories import (
                UserRepositoryImpl, RolePermissionRepositoryImpl, TokenRepositoryImpl
            )
            from auth_service.domain.domain_services import AuthenticationService
            
            user_repo = UserRepositoryImpl()
            auth_service = AuthenticationService(user_repo, None)
            
            handler = RegisterUserHandler(user_repo, auth_service)
            result = handler.handle(command)
            
            if result.success:
                return Response({
                    'success': True,
                    'user_id': result.user_id,
                    'message': result.message
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'message': result.message
                }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """POST /api/auth/login"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """User login"""
        try:
            serializer = LoginRequestSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            command = LoginUserCommand(
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password'],
                ip_address=serializer.validated_data.get('ip_address')
            )
            
            from auth_service.infrastructure.persistence.repositories import (
                UserRepositoryImpl, TokenRepositoryImpl
            )
            from auth_service.domain.domain_services import (
                AuthenticationService, TokenManagementService
            )
            
            user_repo = UserRepositoryImpl()
            token_repo = TokenRepositoryImpl()
            auth_service = AuthenticationService(user_repo, token_repo)
            token_service = TokenManagementService(token_repo)
            
            handler = LoginUserHandler(user_repo, auth_service, token_service)
            result = handler.handle(command)
            
            if result.success:
                return Response({
                    'success': True,
                    'access_token': result.access_token,
                    'refresh_token': result.refresh_token,
                    'expires_in': result.expires_in,
                    'user_id': result.user_id,
                    'message': result.message
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': result.message
                }, status=status.HTTP_401_UNAUTHORIZED)
        
        except Exception as e:
            logger.error(f"Login error: {e}")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """POST /api/auth/logout"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """User logout"""
        try:
            token = request.META.get('HTTP_AUTHORIZATION', '').replace('Bearer ', '')
            user_id = request.user.id if hasattr(request.user, 'id') else None
            
            if not user_id or not token:
                return Response({
                    'success': False,
                    'message': 'Missing user_id or token'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            command = LogoutUserCommand(
                user_id=user_id,
                token=token
            )
            
            from auth_service.infrastructure.persistence.repositories import TokenRepositoryImpl
            
            token_repo = TokenRepositoryImpl()
            handler = LogoutUserHandler(token_repo)
            success = handler.handle(command)
            
            if success:
                return Response({
                    'success': True,
                    'message': 'Logged out successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': 'Logout failed'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class ValidateTokenView(APIView):
    """POST /api/auth/validate"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Validate token"""
        try:
            token = request.data.get('token')
            if not token:
                return Response({
                    'valid': False,
                    'message': 'Token required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            command = ValidateTokenCommand(token=token)
            
            from auth_service.infrastructure.persistence.repositories import TokenRepositoryImpl
            from auth_service.domain.domain_services import TokenManagementService
            
            token_repo = TokenRepositoryImpl()
            token_service = TokenManagementService(token_repo)
            
            handler = ValidateTokenHandler(token_service)
            result = handler.handle(command)
            
            if result.valid:
                return Response({
                    'valid': True,
                    'user_id': result.user_id,
                    'email': result.email,
                    'roles': result.roles,
                    'expires_at': result.expires_at
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'valid': False,
                    'message': result.message
                }, status=status.HTTP_401_UNAUTHORIZED)
        
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return Response({
                'valid': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class CheckAccessView(APIView):
    """POST /api/auth/check-access"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Check user access"""
        try:
            serializer = CheckAccessRequestSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            from auth_service.application.commands_queries import CheckAccessQuery
            from auth_service.infrastructure.persistence.repositories import (
                UserRepositoryImpl, RolePermissionRepositoryImpl
            )
            from auth_service.domain.domain_services import AuthorizationService
            
            user_repo = UserRepositoryImpl()
            role_repo = RolePermissionRepositoryImpl()
            authz_service = AuthorizationService(role_repo)
            
            handler = CheckAccessHandler(user_repo, authz_service)
            result = handler.handle(CheckAccessQuery(
                user_id=serializer.validated_data['user_id'],
                resource=serializer.validated_data['resource'],
                action=serializer.validated_data['action']
            ))
            
            return Response({
                'granted': result.granted,
                'reason': result.reason
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Access check error: {e}")
            return Response({
                'granted': False,
                'reason': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class GetUserView(APIView):
    """GET /api/auth/users/{user_id}"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, user_id):
        """Get user details"""
        try:
            from auth_service.application.commands_queries import GetUserByIdQuery
            from auth_service.infrastructure.persistence.repositories import UserRepositoryImpl
            
            user_repo = UserRepositoryImpl()
            handler = GetUserByIdHandler(user_repo)
            result = handler.handle(GetUserByIdQuery(user_id=user_id))
            
            if result:
                return Response({
                    'success': True,
                    'user': {
                        'user_id': result.user_id,
                        'email': result.email,
                        'roles': result.roles,
                        'is_active': result.is_active,
                        'is_locked': result.is_locked,
                        'created_at': result.created_at
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': 'User not found'
                }, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            logger.error(f"Get user error: {e}")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class AssignRoleView(APIView):
    """POST /api/auth/assign-role"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Assign role to user"""
        try:
            serializer = AssignRoleRequestSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            command = AssignRoleCommand(
                user_id=serializer.validated_data['user_id'],
                role=serializer.validated_data['role'],
                assigned_by=serializer.validated_data.get('assigned_by', 'SYSTEM')
            )
            
            from auth_service.infrastructure.persistence.repositories import UserRepositoryImpl
            
            user_repo = UserRepositoryImpl()
            handler = AssignRoleHandler(user_repo)
            result = handler.handle(command)
            
            if result.success:
                return Response({
                    'success': True,
                    'message': result.message
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': result.message
                }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.error(f"Assign role error: {e}")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class HealthCheckView(APIView):
    """GET /api/auth/health"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Health check"""
        return Response({
            'status': 'healthy',
            'service': 'auth-service',
            'version': '1.0.0'
        }, status=status.HTTP_200_OK)
