"""Service layer package separating business logic from route handlers.

Flow:
API Route -> Validation / Schema -> Service Layer -> Database / ML / Safety / AI
"""

from backend.app.services.agent_service import AgentService, agent_service
from backend.app.services.chat_service import ChatService, chat_service
from backend.app.services.coordination_service import CoordinationService, coordination_service
from backend.app.services.health_service import (
    HealthRecordService,
    SymptomService,
    health_record_service,
    symptom_service,
)
from backend.app.services.prediction_service import PredictionService, prediction_service

__all__ = [
    "AgentService",
    "agent_service",
    "ChatService",
    "chat_service",
    "CoordinationService",
    "coordination_service",
    "HealthRecordService",
    "health_record_service",
    "SymptomService",
    "symptom_service",
    "PredictionService",
    "prediction_service",
]
