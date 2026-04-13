"""
API Gateway - Configuration and setup
"""

# API Gateway Configuration
GATEWAY_CONFIG = {
    'bind': '0.0.0.0:8000',
    'workers': 4,
    'timeout': 60,
    'max_requests': 1000,
    'backlog': 2048,
}

# Service Registry
SERVICE_REGISTRY = {
    'patient-service': {
        'url': 'http://patient-service:8001',
        'prefix': '/api/patients',
        'timeout': 30,
        'retries': 2,
    },
    'pharmacy-service': {
        'url': 'http://pharmacy-service:8002',
        'prefix': '/api/pharmacy',
        'timeout': 30,
        'retries': 2,
    },
    'dispensing-service': {
        'url': 'http://dispensing-service:8003',
        'prefix': '/api/dispensing',
        'timeout': 30,
        'retries': 2,
    },
    'prescription-service': {
        'url': 'http://prescription-service:8004',
        'prefix': '/api/prescriptions',
        'timeout': 30,
        'retries': 2,
    },
    'clinical-advisory-service': {
        'url': 'http://clinical-advisory-service:8005',
        'prefix': '/api/consultations',
        'timeout': 30,
        'retries': 2,
    },
    'auth-service': {
        'url': 'http://auth-service:8006',
        'prefix': '/api/auth',
        'timeout': 15,
        'retries': 1,
        'public': ['register', 'login', 'validate'],
    },
}

# Rate Limiting Configuration
RATE_LIMITING_CONFIG = {
    'enabled': True,
    'default_requests_per_minute': 100,
    'default_requests_per_hour': 5000,
    'per_service': {
        'auth-service': {
            'requests_per_minute': 50,
            'requests_per_hour': 1000,
        },
        'patient-service': {
            'requests_per_minute': 200,
            'requests_per_hour': 10000,
        },
    }
}

# CORS Configuration
CORS_CONFIG = {
    'allowed_origins': [
        'http://localhost:3000',
        'http://localhost:8080',
        'https://example.com',
    ],
    'allowed_methods': ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'],
    'allowed_headers': ['*'],
    'max_age': 3600,
}

# Logging Configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[%(asctime)s] %(name)s - %(levelname)s - %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console']
    }
}

# Health Check Configuration
HEALTH_CHECK_CONFIG = {
    'interval': 30,  # seconds
    'timeout': 5,    # seconds
    'unhealthy_threshold': 3,  # consecutive failures
    'healthy_threshold': 1,
}
