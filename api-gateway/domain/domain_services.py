"""
API Gateway - Domain Layer - Domain Services
Request routing, rate limiting, and service health management
"""

import logging
from typing import Optional, Tuple
from shared_ddd.base import DomainService
from api_gateway.domain.entities import (
    RouteConfiguration, RateLimiter, ServiceHealthCheck, RequestContext,
    RouteId, ServiceEndpoint, RateLimitPolicy, ClientId
)
from api_gateway.domain.events import (
    RequestRouted, RateLimitExceeded, ServiceHealthStatusChanged
)
import time

logger = logging.getLogger(__name__)


class RoutingService(DomainService):
    """Handle request routing to appropriate service"""
    
    def __init__(self, route_repository):
        self.route_repository = route_repository
    
    def find_route(self, path: str, method: str) -> Optional[ServiceEndpoint]:
        """Find matching route for request"""
        try:
            # Try exact path match first
            routes = self.route_repository.get_routes_by_path(path, method)
            
            if routes:
                for route in routes:
                    if route.is_enabled:
                        logger.info(f"Route found: {path} {method} -> {route.endpoint.service_name}")
                        return route.endpoint
            
            # Try pattern matching (e.g., /api/patients/{id})
            pattern_routes = self.route_repository.get_pattern_routes(path)
            
            for route in pattern_routes:
                if route.endpoint.method == method and route.is_enabled:
                    logger.info(f"Pattern route found: {path} {method} -> {route.endpoint.service_name}")
                    return route.endpoint
            
            logger.warning(f"No route found: {path} {method}")
            return None
        
        except Exception as e:
            logger.error(f"Routing error: {e}")
            return None
    
    def extract_path_parameters(self, pattern: str, path: str) -> dict:
        """Extract URL parameters from request path"""
        # Simple parameter extraction for {id}, {name}, etc
        import re
        
        params = {}
        # Convert pattern /api/users/{id} to regex
        pattern_regex = pattern.replace('{', '(?P<').replace('}', '>[^/]+)')
        
        match = re.match(f"^{pattern_regex}$", path)
        if match:
            params = match.groupdict()
        
        return params


class RateLimitingService(DomainService):
    """Handle rate limiting"""
    
    def __init__(self):
        self.limiters = {}  # {service_name: {client_id: RateLimiter}}
        self.default_policy = RateLimitPolicy(
            requests_per_minute=100,
            requests_per_hour=5000
        )
    
    def check_rate_limit(self, service_name: str, client_id: str,
                         policy: Optional[RateLimitPolicy] = None) -> Tuple[bool, str]:
        """Check if request is within rate limits"""
        try:
            policy = policy or self.default_policy
            
            if service_name not in self.limiters:
                self.limiters[service_name] = {}
            
            service_limiters = self.limiters[service_name]
            
            if client_id not in service_limiters:
                service_limiters[client_id] = RateLimiter(policy)
            
            limiter = service_limiters[client_id]
            
            if not limiter.check_limit(client_id):
                logger.warning(f"Rate limit exceeded: {service_name} by {client_id}")
                return False, "Rate limit exceeded"
            
            return True, "OK"
        
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Fail open on errors
            return True, "OK"
    
    def get_rate_limit_headers(self, service_name: str, client_id: str,
                               policy: RateLimitPolicy) -> dict:
        """Get rate limit headers for response"""
        try:
            if service_name not in self.limiters:
                return {}
            
            service_limiters = self.limiters[service_name]
            if client_id not in service_limiters:
                return {}
            
            limiter = service_limiters[client_id]
            
            now = int(time.time())
            minute_bucket = now // 60
            hour_bucket = now // 3600
            
            minute_remaining = max(0, policy.requests_per_minute - 
                                   limiter.requests_by_minute.get(minute_bucket, 0))
            hour_remaining = max(0, policy.requests_per_hour -
                                limiter.requests_by_hour.get(hour_bucket, 0))
            
            return {
                'X-RateLimit-Limit-Per-Minute': str(policy.requests_per_minute),
                'X-RateLimit-Remaining-Minute': str(minute_remaining),
                'X-RateLimit-Limit-Per-Hour': str(policy.requests_per_hour),
                'X-RateLimit-Remaining-Hour': str(hour_remaining),
            }
        
        except Exception as e:
            logger.error(f"Get rate limit headers error: {e}")
            return {}


class ServiceHealthService(DomainService):
    """Manage service health checking"""
    
    def __init__(self):
        self.health_checks = {}  # {service_name: ServiceHealthCheck}
    
    def register_service(self, service_name: str, check_url: str):
        """Register service for health checking"""
        self.health_checks[service_name] = ServiceHealthCheck(service_name, check_url)
    
    def mark_service_healthy(self, service_name: str) -> bool:
        """Mark service as healthy and return if status changed"""
        try:
            if service_name not in self.health_checks:
                return False
            
            status_changed = self.health_checks[service_name].mark_healthy()
            
            if status_changed:
                logger.info(f"Service recovered: {service_name}")
            
            return status_changed
        
        except Exception as e:
            logger.error(f"Mark healthy error: {e}")
            return False
    
    def mark_service_unhealthy(self, service_name: str) -> bool:
        """Mark service as unhealthy and return if status changed"""
        try:
            if service_name not in self.health_checks:
                return False
            
            status_changed = self.health_checks[service_name].mark_unhealthy()
            
            if status_changed:
                logger.warning(f"Service marked as unhealthy: {service_name}")
            
            return status_changed
        
        except Exception as e:
            logger.error(f"Mark unhealthy error: {e}")
            return False
    
    def is_service_healthy(self, service_name: str) -> bool:
        """Check if service is healthy"""
        try:
            if service_name not in self.health_checks:
                return False
            
            return self.health_checks[service_name].is_healthy
        
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return False
    
    def get_healthy_services(self) -> list:
        """Get all healthy services"""
        try:
            healthy = []
            for service_name, health_check in self.health_checks.items():
                if health_check.is_healthy:
                    healthy.append(service_name)
            return healthy
        
        except Exception as e:
            logger.error(f"Get healthy services error: {e}")
            return []


class AuthenticationService(DomainService):
    """Handle authentication as part of gateway"""
    
    def __init__(self, auth_service_url: str):
        self.auth_service_url = auth_service_url
    
    def validate_token(self, token: str) -> Tuple[bool, Optional[dict]]:
        """Validate JWT token with auth service"""
        try:
            # In real implementation, would call auth service
            # For now, simplified validation
            if not token or len(token) < 20:
                return False, None
            
            logger.info("Token validated (simplified)")
            return True, {"user_id": "user_123", "roles": ["PATIENT"]}
        
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return False, None
    
    def check_authorization(self, user_info: dict, required_roles: list) -> bool:
        """Check if user has required roles"""
        try:
            user_roles = user_info.get('roles', [])
            
            if not required_roles:
                return True
            
            for role in required_roles:
                if role in user_roles:
                    return True
            
            return False
        
        except Exception as e:
            logger.error(f"Authorization check error: {e}")
            return False


class RequestValidationService(DomainService):
    """Validate incoming requests"""
    
    def validate_request(self, context: RequestContext) -> Tuple[bool, str]:
        """Validate request format and content"""
        try:
            # Check method
            valid_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
            if context.method not in valid_methods:
                return False, f"Invalid HTTP method: {context.method}"
            
            # Check path
            if not context.path or not context.path.startswith('/'):
                return False, "Invalid path"
            
            # Check client ID
            if not context.client_id:
                return False, "Missing client ID"
            
            # Check body size (limit to 10MB)
            import json
            body_size = len(json.dumps(context.body))
            if body_size > 10 * 1024 * 1024:
                return False, "Request body too large"
            
            return True, "OK"
        
        except Exception as e:
            logger.error(f"Request validation error: {e}")
            return False, str(e)


class ResponseProcessingService(DomainService):
    """Process responses from services"""
    
    def aggregate_responses(self, responses: list) -> dict:
        """Aggregate multiple service responses"""
        try:
            aggregated = {
                'success': all(r.get('success', False) for r in responses),
                'data': responses,
                'count': len(responses)
            }
            return aggregated
        
        except Exception as e:
            logger.error(f"Response aggregation error: {e}")
            return {}
    
    def transform_response(self, response: dict, transform_rules: dict = None) -> dict:
        """Transform response based on rules"""
        try:
            if not transform_rules:
                return response
            
            # Apply transformations
            for rule in transform_rules:
                if rule.get('type') == 'rename':
                    old_key = rule.get('from')
                    new_key = rule.get('to')
                    if old_key in response:
                        response[new_key] = response.pop(old_key)
            
            return response
        
        except Exception as e:
            logger.error(f"Response transformation error: {e}")
            return response
