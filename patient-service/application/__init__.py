"""
Patient Application Layer

Contains application logic and use cases:
- Commands and command handlers
- Queries and query handlers
- DTOs (Data Transfer Objects)
"""

from .commands import (
    RegisterPatientCommand, UpdatePatientInsuranceCommand,
    UpdatePatientContactCommand, UpdatePatientAddressCommand,
    DeactivatePatientCommand
)
from .command_handlers import (
    RegisterPatientCommandHandler, UpdatePatientInsuranceCommandHandler,
    UpdatePatientContactCommandHandler, UpdatePatientAddressCommandHandler,
    DeactivatePatientCommandHandler
)
from .queries import (
    GetPatientByIdQuery, GetPatientByAccountIdQuery,
    GetPatientByEmailQuery, ListAllPatientsQuery,
    ListInsuredPatientsQuery, GetPatientMedicalRecordsQuery
)
from .query_handlers import (
    GetPatientByIdQueryHandler, GetPatientByAccountIdQueryHandler,
    GetPatientByEmailQueryHandler, ListAllPatientsQueryHandler,
    ListInsuredPatientsQueryHandler, GetPatientMedicalRecordsQueryHandler
)

__all__ = [
    # Commands
    "RegisterPatientCommand", "UpdatePatientInsuranceCommand",
    "UpdatePatientContactCommand", "UpdatePatientAddressCommand",
    "DeactivatePatientCommand",
    # Command Handlers
    "RegisterPatientCommandHandler", "UpdatePatientInsuranceCommandHandler",
    "UpdatePatientContactCommandHandler", "UpdatePatientAddressCommandHandler",
    "DeactivatePatientCommandHandler",
    # Queries
    "GetPatientByIdQuery", "GetPatientByAccountIdQuery",
    "GetPatientByEmailQuery", "ListAllPatientsQuery",
    "ListInsuredPatientsQuery", "GetPatientMedicalRecordsQuery",
    # Query Handlers
    "GetPatientByIdQueryHandler", "GetPatientByAccountIdQueryHandler",
    "GetPatientByEmailQueryHandler", "ListAllPatientsQueryHandler",
    "ListInsuredPatientsQueryHandler", "GetPatientMedicalRecordsQueryHandler",
]
