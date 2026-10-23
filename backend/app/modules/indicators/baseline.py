"""Context snapshot, not a macroeconomic or national-budget prediction."""

import hashlib
import json
from datetime import UTC, datetime

from sqlalchemy import select

from app.modules.indicators.auxiliary import AUXILIARY_CODES
from app.modules.indicators.fiscal_baseline import current as current_fiscal
from app.modules.indicators.models import Indicator
from app.modules.indicators.service import view


def current(session):
    indicators = [
        view(session, row)
        for row in session.scalars(
            select(Indicator)
            .where(Indicator.is_active.is_(True), Indicator.code.not_in(AUXILIARY_CODES))
            .order_by(Indicator.code)
        )
    ]
    observations = [
        {
            "code": item["code"],
            "name": item["name"],
            "unit": item["unit"],
            "scope": item["scope"],
            "frequency": item["frequency"],
            "methodology": item["methodology"],
            "observation": item["latest"],
        }
        for item in indicators
        if item["latest"] and not item["latest"]["source"].get("is_example")
    ]
    fiscal = current_fiscal(session)
    canonical = json.dumps(
        {"observations": observations, "fiscal": fiscal},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return {
        "id": hashlib.sha256(canonical.encode()).hexdigest(),
        "captured_at": datetime.now(UTC).isoformat(),
        "status": "PARTIAL" if observations else "EMPTY",
        "kind": "CONTEXT_WITH_FISCAL" if fiscal["status"] == "AVAILABLE" else "CONTEXT_ONLY",
        "fiscal": fiscal,
        "observations": observations,
        "missing": [
            *fiscal["missing"],
            "Recortes fiscais de estados e municípios e premissas explícitas de cenários futuros",
            "Contextos revisados sobre causas e consequências",
        ],
        "limitations": [
            "Cada indicador conserva sua referência; períodos e abrangências podem diferir.",
            (
                "Esta base contextual não é somada ao saldo incremental e não prevê PIB, "
                "emprego ou dívida."
            ),
        ],
    }
