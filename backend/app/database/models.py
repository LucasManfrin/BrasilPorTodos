"""Explicit model registry for Alembic and application services."""

from app.modules.admin.models import AuditEvent
from app.modules.auth.models import AuthRateLimit, AuthSession, RefreshToken
from app.modules.contexts.models import Context, ContextPublication, ContextReview, ContextVersion
from app.modules.graphs.models import (
    GraphCollection,
    GraphCollectionPublication,
    GraphCollectionVersion,
    GraphEdge,
    GraphEdgePublication,
    GraphEdgeReview,
    GraphEdgeVersion,
    GraphNode,
    GraphNodeVersion,
)
from app.modules.guidance.models import GuidanceCall
from app.modules.ideas.models import Idea, IdeaReport, IdeaSuggestion
from app.modules.indicators.collection import CollectionRun
from app.modules.indicators.models import (
    FiscalSpendingCohort,
    GeneralGovernmentCohort,
    Indicator,
    IndicatorValue,
)
from app.modules.plans.models import Plan, PlanPolicy, PlanVersion
from app.modules.policies.models import (
    FinancialImpact,
    Policy,
    PolicyFunding,
    PolicySource,
    PolicyVersion,
)
from app.modules.simulations.models import Simulation, SimulationResult
from app.modules.sources.models import Source
from app.modules.users.models import User

__all__ = [
    "GuidanceCall",
    "Idea",
    "IdeaReport",
    "IdeaSuggestion",
    "GraphNode",
    "GraphNodeVersion",
    "GraphEdge",
    "GraphEdgeVersion",
    "GraphEdgeReview",
    "GraphEdgePublication",
    "GraphCollection",
    "GraphCollectionVersion",
    "GraphCollectionPublication",
    "Context",
    "ContextVersion",
    "ContextReview",
    "ContextPublication",
    "AuditEvent",
    "CollectionRun",
    "AuthRateLimit",
    "AuthSession",
    "RefreshToken",
    "FinancialImpact",
    "Indicator",
    "IndicatorValue",
    "FiscalSpendingCohort",
    "GeneralGovernmentCohort",
    "Plan",
    "PlanPolicy",
    "PlanVersion",
    "Policy",
    "PolicyFunding",
    "PolicySource",
    "PolicyVersion",
    "Simulation",
    "SimulationResult",
    "Source",
    "User",
]
