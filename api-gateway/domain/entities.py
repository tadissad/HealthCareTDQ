"""
API Gateway - Domain Layer - Value Objects and Entities
Request routing, rate limiting, and gateway management
"""

from shared_ddd.base import ValueObject, Aggregate, DomainEvent
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, List
import time


class RouteId(ValueObject):
    """Route identifier"""
    
    def __init__(self, value: str):
        if not value:
            raise ValueError("RouteId cannot be empty")
        self.value = str(value)
    
    def __eq__(self, other):
        return isinstance(other, RouteId) and self.value == other.value
    
    def __hash__(self):
        return hash(self.value)


class ServiceEndpoint(ValueObject):
    """Service endpoint configuration"""
    
    def __init__(self, service_name: str, url: str, method: str, path: str):
        if not all([service_name, url, method, path]):
            raise ValueError("All endpoint parameters required")
        self.service_name = service_name
        self.url = url
        self.method = method.upper()
        self.path = path
    
    def __eq__(self, other):
        return (isinstance(other, ServiceEndpoint) and 
                self.url == other.url and 
                self.method == other.method)
    
    def __hash__(self):
        return hash((self.url, self.method))


class RateLimitPolicy(ValueObject):
    """Rate limiting policy"""
    
    def __init__(self, requests_per_minute: int, requests_per_hour: int):
        if requests_per_minute <= 0 or requests_per_hour <= 0:
            raise ValueError("Rate limits must be positive")
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
    
    def __eq__(self, other):
        return (isinstance(other, RateLimitPolicy) and 
                self.requests_per_minute == other.requests_per_minute and
                self.requests_per_hour == other.requests_per_hour)


class ClientId(ValueObject):
    """Client/User identifier for rate limiting"""
    
    def __init__(self, value: str):
        if not value:
            raise ValueError("ClientId cannot be empty")
        self.value = str(value)
    
    def __eq__(self, other):
        return isinstance(other, ClientId) and self.value == other.value
    
    def __hash__(self):
        return hash(self.value)


# ============ EVENTS ============

@dataclass
class RequestRouted(DomainEvent):
    """Request routed to service"""
    route_id: str
    client_id: str
    service_name: str
    path: str
    method: str
    timestamp: int
    event_type: str = "RequestRouted"


@dataclass
class RateLimitExceeded(DomainEvent):
    """Rate limit exceeded"""
    client_id: str
    service_name: str
    limit_type: str  # MINUTE or HOUR
    timestamp: int
    event_type: str = "RateLimitExceeded"


@dataclass
class ServiceHealthStatusChanged(DomainEvent):
    """Service health status changed"""
    service_name: str
    is_healthy: bool
    reason: str
    timestamp: int
    event_type: str = "ServiceHealthStatusChanged"


@dataclass
class GatewayConfigurationUpdated(DomainEvent):
    """Gateway configuration updated"""
    changed_fields: List[str]
    timestamp: int
    event_type: str = "GatewayConfigurationUpdated"


# ============ ENTITIES ============

class RouteConfiguration(Aggregate):
    """Route configuration aggregate"""
    
    def __init__(self, route_id: RouteId, endpoint: ServiceEndpoint):
        super().__init__()
        self.route_id = route_id
        self.endpoint = endpoint
        self.is_enabled = True
        self.rate_limit = RateLimitPolicy(
            requests_per_minute=100,
            requests_per_hour=5000
        )
        self.created_at = int(time.time())
    
    def disable(self):
        """Disable route"""
        self.is_enabled = False
    
    def enable(self):
        """Enable route"""
        self.is_enabled = True
    
    def update_rate_limit(self, policy: RateLimitPolicy):
        """Update rate limiting policy"""
        self.rate_limit = policy
        self.domain_events.append(GatewayConfigurationUpdated(
            changed_fields=['rate_limit'],
            timestamp=int(time.time())
        ))


class RateLimiter:
    """Rate limiting tracker"""
    
    def __init__(self, policy: RateLimitPolicy):
        self.policy = policy
        self.requests_by_minute = {}  # {minute_bucket: count}
        self.requests_by_hour = {}    # {hour_bucket: count}
    
    def check_limit(self, client_id: str) -> bool:
        """Check if request is within limits"""
        now = int(time.time())
        minute_bucket = now // 60
        hour_bucket = now // 3600
        
        # Cleanup old buckets
        self._cleanup_old_buckets(minute_bucket, hour_bucket)
        
        # Check minute limit
        minute_count = self.requests_by_minute.get(minute_bucket, 0)
        if minute_count >= self.policy.requests_per_minute:
            return False
        
        # Check hour limit
        hour_count = self.requests_by_hour.get(hour_bucket, 0)
        if hour_count >= self.policy.requests_per_hour:
            return False
        
        # Record request
        self.requests_by_minute[minute_bucket] = minute_count + 1
        self.requests_by_hour[hour_bucket] = hour_count + 1
        
        return True
    
    def _cleanup_old_buckets(self, current_minute: int, current_hour: int):
        """Remove old buckets"""
        # Keep last 2 minute buckets
        for key in list(self.requests_by_minute.keys()):
            if key < current_minute - 2:
                del self.requests_by_minute[key]
        
        # Keep last 2 hour buckets
        for key in list(self.requests_by_hour.keys()):
            if key < current_hour - 2:
                del self.requests_by_hour[key]


class ServiceHealthCheck:
    """Service health status"""
    
    def __init__(self, service_name: str, check_url: str):
        self.service_name = service_name
        self.check_url = check_url
        self.is_healthy = True
        self.last_check_at = None
        self.failure_count = 0
        self.consecutive_failures = 0
    
    def mark_healthy(self):
        """Mark service as healthy"""
        was_healthy = self.is_healthy
        self.is_healthy = True
        self.failure_count = 0
        self.consecutive_failures = 0
        self.last_check_at = int(time.time())
        
        if not was_healthy:
            return True  # Status changed
        return False
    
    def mark_unhealthy(self):
        """Mark service as unhealthy"""
        was_healthy = self.is_healthy
        self.consecutive_failures += 1
        self.failure_count += 1
        self.last_check_at = int(time.time())
        
        # Consider unhealthy after 3 failures
        if self.consecutive_failures >= 3:
            self.is_healthy = False
        
        return was_healthy  # Status changed


class RequestContext:
    """Context for gateway request"""
    
    def __init__(self, client_id: str, path: str, method: str, 
                 headers: Dict = None, body: Dict = None):
        self.client_id = client_id
        self.path = path
        self.method = method.upper()
        self.headers = headers or {}
        self.body = body or {}
        self.request_id = str(time.time() * 1000)
        self.created_at = int(time.time())
    
    def get_authorization_token(self) -> Optional[str]:
        """Extract authorization token from headers"""
        auth_header = self.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            return auth_header[7:]
        return None
    
    def requires_authentication(self) -> bool:
        """Check if this request requires authentication"""
        # Public endpoints that don't need auth
        public_paths = [
            '/api/auth/register',
            '/api/auth/login',
            '/api/auth/validate',
            '/health',
        ]
        
        for public_path in public_paths:
            if self.path.startswith(public_path):
                return False
        
        return True
