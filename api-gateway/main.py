"""
API Gateway - Infrastructure Layer - FastAPI Application
HTTP gateway with routing, rate limiting, and authentication
"""

import logging
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import time
from typing import Optional
from api_gateway.domain.domain_services import (
    RoutingService, RateLimitingService, ServiceHealthService,
    AuthenticationService, RequestValidationService, ResponseProcessingService
)
from api_gateway.domain.entities import RequestContext

logger = logging.getLogger(__name__)


def create_gateway_app(config: dict) -> FastAPI:
    """Create FastAPI gateway application"""
    
    app = FastAPI(
        title="health-micro-ai API Gateway",
        version="1.0.0",
        description="Central API gateway for health microservices"
    )
    
    # Initialize services
    routing_service = RoutingService(None)  # Would be injected with repository
    rate_limiting_service = RateLimitingService()
    health_service = ServiceHealthService()
    auth_service = AuthenticationService(config.get('auth_service_url', 'http://auth-service:8000'))
    validation_service = RequestValidationService()
    response_service = ResponseProcessingService()
    
    # Register services for health checking
    services_config = config.get('services', {})
    for service_name, service_config in services_config.items():
        health_service.register_service(
            service_name,
            service_config.get('health_check_url')
        )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # ============ MIDDLEWARE ============
    
    @app.middleware("http")
    async def add_correlation_id(request: Request, call_next):
        """Add correlation ID for tracing"""
        correlation_id = request.headers.get("X-Correlation-ID", str(time.time()))
        request.state.correlation_id = correlation_id
        
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response
    
    @app.middleware("http")
    async def timing_middleware(request: Request, call_next):
        """Add request timing"""
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        response.headers["X-Process-Time"] = str(process_time)
        logger.info(f"Request completed in {process_time:.3f}s: {request.method} {request.url.path}")
        return response
    
    # ============ HEALTH CHECKS ============
    
    @app.get("/health")
    async def gateway_health():
        """Gateway health check"""
        return {
            "status": "healthy",
            "service": "api-gateway",
            "version": "1.0.0",
            "timestamp": int(time.time())
        }
    
    @app.get("/health/services")
    async def services_health():
        """Check all downstream services health"""
        healthy_services = health_service.get_healthy_services()
        return {
            "healthy_services": healthy_services,
            "total_services": len(health_service.health_checks),
            "status": "all_healthy" if len(healthy_services) == len(health_service.health_checks) else "degraded"
        }
    
    # ============ GATEWAY ENDPOINTS ============
    
    @app.get("/api/info")
    async def gateway_info():
        """Gateway information"""
        return {
            "name": "health-micro-ai API Gateway",
            "version": "1.0.0",
            "services": list(services_config.keys()),
            "upstream_services": config.get('services', {})
        }
    
    # ============ REQUEST ROUTING ============
    
    @app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
    async def gateway_route(
        full_path: str,
        request: Request,
        authorization: Optional[str] = Header(None)
    ):
        """Route requests to appropriate microservice"""
        try:
            # Extract client ID (from token or IP)
            client_id = request.headers.get("X-Client-ID") or request.client.host
            
            # Create request context
            body = {}
            try:
                body = await request.json()
            except:
                pass
            
            context = RequestContext(
                client_id=client_id,
                path=f"/{full_path}",
                method=request.method,
                headers=dict(request.headers),
                body=body
            )
            
            # Validate request
            valid, message = validation_service.validate_request(context)
            if not valid:
                logger.warning(f"Invalid request: {message}")
                raise HTTPException(status_code=400, detail=message)
            
            # Check authentication if required
            if context.requires_authentication():
                if not authorization:
                    raise HTTPException(status_code=401, detail="Missing authorization")
                
                token = authorization.replace("Bearer ", "")
                valid_token, user_info = auth_service.validate_token(token)
                
                if not valid_token:
                    raise HTTPException(status_code=401, detail="Invalid token")
                
                request.state.user = user_info
            
            # Find route
            endpoint = routing_service.find_route(context.path, request.method)
            if not endpoint:
                raise HTTPException(status_code=404, detail="Route not found")
            
            # Check rate limiting
            service_name = endpoint.service_name
            rate_limited, message = rate_limiting_service.check_rate_limit(
                service_name,
                client_id
            )
            
            if not rate_limited:
                # Mark service unhealthy after rate limit failure
                health_service.mark_service_unhealthy(service_name)
                raise HTTPException(status_code=429, detail="Rate limit exceeded")
            
            # Check service health
            if not health_service.is_service_healthy(service_name):
                logger.warning(f"Service {service_name} is unhealthy")
                raise HTTPException(status_code=503, detail=f"Service {service_name} unavailable")
            
            # Forward request to service
            async with httpx.AsyncClient() as client:
                try:
                    # Build target URL
                    target_url = f"{endpoint.url}{context.path}"
                    
                    # Forward request
                    response = await client.request(
                        method=request.method,
                        url=target_url,
                        headers={
                            k: v for k, v in request.headers.items()
                            if k.lower() not in ['host', 'connection']
                        },
                        json=body if body else None,
                        timeout=10.0
                    )
                    
                    # Mark service as healthy on success
                    health_service.mark_service_healthy(service_name)
                    
                    # Get response
                    response_body = await response.aread()
                    
                    # Add rate limit headers
                    headers = dict(response.headers)
                    headers.update(rate_limiting_service.get_rate_limit_headers(
                        service_name, client_id, None
                    ))
                    
                    return JSONResponse(
                        content=response_body,
                        status_code=response.status_code,
                        headers=headers
                    )
                
                except httpx.TimeoutException:
                    logger.error(f"Request timeout to {service_name}")
                    health_service.mark_service_unhealthy(service_name)
                    raise HTTPException(status_code=504, detail="Request timeout")
                except Exception as e:
                    logger.error(f"Request forwarding error: {e}")
                    health_service.mark_service_unhealthy(service_name)
                    raise HTTPException(status_code=502, detail="Bad gateway")
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Gateway routing error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    return app


# ============ FACTORY FUNCTION ============

def create_app():
    """Create default gateway app with example config"""
    config = {
        'auth_service_url': 'http://auth-service:8000',
        'services': {
            'patient-service': {
                'url': 'http://patient-service:8001',
                'health_check_url': 'http://patient-service:8001/health'
            },
            'pharmacy-service': {
                'url': 'http://pharmacy-service:8002',
                'health_check_url': 'http://pharmacy-service:8002/health'
            },
            'dispensing-service': {
                'url': 'http://dispensing-service:8003',
                'health_check_url': 'http://dispensing-service:8003/health'
            },
            'prescription-service': {
                'url': 'http://prescription-service:8004',
                'health_check_url': 'http://prescription-service:8004/health'
            },
            'clinical-advisory-service': {
                'url': 'http://clinical-advisory-service:8005',
                'health_check_url': 'http://clinical-advisory-service:8005/health'
            },
            'auth-service': {
                'url': 'http://auth-service:8006',
                'health_check_url': 'http://auth-service:8006/health'
            },
        }
    }
    
    return create_gateway_app(config)


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
