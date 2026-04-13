"""
Auth Service - Infrastructure Layer - ORM Models
Django models for User, Role, Token persistence
"""

from django.db import models
from django.contrib.auth.hashers import make_password, check_password
import json


class UserModel(models.Model):
    """ORM model for User aggregate"""
    
    ROLE_CHOICES = [
        ('ADMIN', 'Administrator'),
        ('CLINICIAN', 'Clinician'),
        ('PHARMACIST', 'Pharmacist'),
        ('PATIENT', 'Patient'),
        ('NURSE', 'Nurse'),
        ('MANAGER', 'Manager'),
        ('STAFF', 'Staff'),
    ]
    
    # Identifiers
    user_id = models.CharField(max_length=50, unique=True, db_index=True)
    email = models.EmailField(unique=True, db_index=True)
    
    # Authentication
    password_hash = models.CharField(max_length=255)
    
    # Status
    is_active = models.BooleanField(default=True, db_index=True)
    is_locked = models.BooleanField(default=False)
    failed_login_attempts = models.IntegerField(default=0)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_at = models.DateTimeField(null=True, blank=True)
    locked_until = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'auth_users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_locked']),
        ]
    
    def set_password(self, password: str):
        """Hash and set password"""
        self.password_hash = make_password(password)
    
    def check_password(self, password: str) -> bool:
        """Check password against hash"""
        return check_password(password, self.password_hash)


class UserRoleModel(models.Model):
    """Junction table for User roles"""
    
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name='user_roles')
    role = models.CharField(
        max_length=20,
        choices=UserModel._meta.get_field('role_choices').choices if hasattr(UserModel._meta.get_field('role_choices'), 'choices') else []
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.CharField(max_length=50, default='SYSTEM')
    
    class Meta:
        db_table = 'auth_user_roles'
        unique_together = ('user', 'role')


class RoleModel(models.Model):
    """ORM model for Role"""
    
    name = models.CharField(max_length=50, unique=True, db_index=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'auth_roles'


class PermissionModel(models.Model):
    """ORM model for Permission"""
    
    resource = models.CharField(max_length=100, db_index=True)
    action = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'auth_permissions'
        unique_together = ('resource', 'action')
        indexes = [
            models.Index(fields=['resource', 'action']),
        ]


class RolePermissionModel(models.Model):
    """Junction table for Role permissions"""
    
    role = models.ForeignKey(RoleModel, on_delete=models.CASCADE, related_name='permissions')
    permission = models.ForeignKey(PermissionModel, on_delete=models.CASCADE)
    granted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'auth_role_permissions'
        unique_together = ('role', 'permission')


class TokenModel(models.Model):
    """ORM model for token metadata"""
    
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name='tokens')
    token_hash = models.CharField(max_length=255, unique=True, db_index=True)
    token_type = models.CharField(max_length=20, default='access')  # access, refresh
    expires_at = models.DateTimeField(db_index=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'auth_tokens'
        indexes = [
            models.Index(fields=['user', 'revoked_at']),
            models.Index(fields=['expires_at']),
        ]


class AuthLogModel(models.Model):
    """Log authentication events"""
    
    EVENT_TYPES = [
        ('LOGIN', 'User Login'),
        ('LOGOUT', 'User Logout'),
        ('FAILED_LOGIN', 'Failed Login Attempt'),
        ('TOKEN_GENERATED', 'Token Generated'),
        ('TOKEN_VALIDATED', 'Token Validated'),
        ('TOKEN_INVALID', 'Token Invalid'),
        ('ROLE_ASSIGNED', 'Role Assigned'),
        ('ROLE_REVOKED', 'Role Revoked'),
        ('PERMISSION_GRANTED', 'Permission Granted'),
        ('ACCOUNT_LOCKED', 'Account Locked'),
    ]
    
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, db_index=True)
    user = models.ForeignKey(UserModel, on_delete=models.SET_NULL, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    details = models.JSONField(default=dict, blank=True)
    occurred_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'auth_logs'
        indexes = [
            models.Index(fields=['event_type', 'occurred_at']),
            models.Index(fields=['user', 'occurred_at']),
        ]
