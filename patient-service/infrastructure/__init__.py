"""
Patient Infrastructure Layer

Contains implementation details:
- Persistence (ORM models, repository implementation)
- Event bus and event handlers
- External service integrations
"""

from .persistence.repositories import PatientRepositoryImpl

__all__ = ["PatientRepositoryImpl"]
