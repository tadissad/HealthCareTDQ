"""
views.py – auth-service
========================
Phát hành và xác thực JWT Token cho toàn bộ hệ thống health-micro-ai.

Endpoints:
  POST /auth/login/     – Cấp JWT token cho user đã xác thực
  POST /auth/validate/  – Xác thực JWT token (dùng bởi api-gateway và các service nội bộ)
  GET  /health/         – Health check
"""
import jwt
import datetime
import logging

from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)

JWT_SECRET    = getattr(settings, 'JWT_SECRET',       'health-micro-ai-jwt-secret-key-2024')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRY_HOURS = getattr(settings, 'JWT_EXPIRY_HOURS', 24)


class LoginView(APIView):
    """
    POST /auth/login/
    Body: { "user_id": 1, "username": "nguyenvana", "role": "customer" }
    Trả về: { "token": "eyJ..." }

    NOTE: Service này KHÔNG tự xác thực username/password.
    Api-gateway chịu trách nhiệm kiểm tra credential, rồi gọi endpoint này
    để nhận JWT sau khi xác nhận hợp lệ.
    """
    def post(self, request):
        user_id  = request.data.get('user_id')
        username = request.data.get('username')
        role     = request.data.get('role', 'customer')

        if user_id is None or not username:
            return Response(
                {'error': 'Thiếu user_id hoặc username'},
                status=status.HTTP_400_BAD_REQUEST
            )

        payload = {
            'user_id':  user_id,
            'username': username,
            'role':     role,
            'iat':      datetime.datetime.utcnow(),
            'exp':      datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_EXPIRY_HOURS),
        }

        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        logger.info(f"[AUTH] JWT issued → user_id={user_id} role={role}")

        return Response({'token': token}, status=status.HTTP_200_OK)


class ValidateTokenView(APIView):
    """
    POST /auth/validate/
    Body: { "token": "eyJ..." }
    Trả về: { "valid": true, "user_id": 1, "username": "...", "role": "customer" }
    Hoặc:   { "valid": false, "error": "Token expired" }
    """
    def post(self, request):
        token = request.data.get('token')
        if not token:
            return Response(
                {'valid': False, 'error': 'Token là bắt buộc'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            logger.info(f"[AUTH] Token hợp lệ → user_id={payload.get('user_id')}")
            return Response({
                'valid':    True,
                'user_id':  payload.get('user_id'),
                'username': payload.get('username'),
                'role':     payload.get('role'),
            })

        except jwt.ExpiredSignatureError:
            logger.warning("[AUTH] Token hết hạn")
            return Response(
                {'valid': False, 'error': 'Token đã hết hạn'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except jwt.InvalidTokenError as e:
            logger.warning(f"[AUTH] Token không hợp lệ: {e}")
            return Response(
                {'valid': False, 'error': 'Token không hợp lệ'},
                status=status.HTTP_401_UNAUTHORIZED
            )


class HealthView(APIView):
    """GET /health/ – Kiểm tra trạng thái auth-service"""
    def get(self, request):
        return Response({
            'status':  'UP',
            'service': 'auth-service',
            'version': '1.0.0',
        })
