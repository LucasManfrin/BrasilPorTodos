"""Declared sensitivity of a complete published proposal, never a causal forecast."""

from decimal import ROUND_HALF_UP, Decimal, localcontext

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.simulation.fiscal import EstimateStatus, Impact, ImpactType, PolicyInput, simulate
from app.simulation.version import SIMULATION_ENGINE_VERSION

METHOD_VERSION = "DECLARED_SENSITIVITY_1"
MONEY_LIMIT = Decimal("9999999999999999.99")
UNKNOWN = [
    "Os custos e efeitos foram declarados pelo autor, não verificados pelo cálculo.",
    (
        "A faixa depende dos multiplicadores escolhidos; "
        "não tem probabilidade ou confiança estatística."
    ),
    "Não inclui efeitos sobre emprego, PIB, dívida ou possíveis sobreposições entre medidas.",
    (
        "O financiamento informado não é somado como receita; "
        "só as parcelas explícitas entram na conta."
    ),
]


class Sensitivity(BaseModel):
    model_config = ConfigDict(extra="forbid")
    cost_low: Decimal = Field(default=Decimal("1.00"), ge=0, le=1, decimal_places=4)
    cost_high: Decimal = Field(default=Decimal("1.00"), ge=1, le=2, decimal_places=4)
    gain_low: Decimal = Field(default=Decimal("1.00"), ge=0, le=1, decimal_places=4)
    gain_high: Decimal = Field(default=Decimal("1.00"), ge=1, le=2, decimal_places=4)

    @model_validator(mode="before")
    @classmethod
    def decimal_strings(cls, values):
        if isinstance(values, dict) and any(
            not isinstance(value, (str, Decimal)) for value in values.values()
        ):
            raise ValueError("Multiplicadores devem ser strings decimais.")
        return values


def comparability(rows):
    if not rows:
        return "Não há parcelas estimadas para comparar."
    dimensions = ["fiscal_scope", "accounting_basis", "price_basis", "component", "period_basis"]
    for field in dimensions:
        values = {getattr(row, field) for row in rows}
        if None in values or "UNSPECIFIED" in values:
            return (
                "Faltam recortes fiscais das parcelas; confira abrangência, "
                "critério, preços, componente e período."
            )
        if len(values) != 1:
            return (
                "As parcelas misturam recortes fiscais. Não há um total comparável para esta faixa."
            )
    if rows[0].price_basis == "CONSTANT":
        years = {row.price_base_year for row in rows}
        if None in years or len(years) != 1:
            return "Os valores constantes precisam do mesmo ano-base de preços."
    return None


def analyze(version, assumptions: Sensitivity):
    base = {
        "available": False,
        "method_version": METHOD_VERSION,
        "engine_version": SIMULATION_ENGINE_VERSION,
        "classification": "ESTIMATIVA_DECLARADA",
        "unknowns": UNKNOWN,
        "assumptions": assumptions.model_dump(mode="json"),
        "scenarios": [],
    }
    if not version.proposal_details or version.proposal_details.level != "COMPLETE":
        return {
            **base,
            "reason": "Esta versão não foi publicada como proposta completa pelo novo fluxo.",
        }
    if version.financial_impact_status != "ESTIMATED":
        return {
            **base,
            "reason": (
                "Sem estimativa fiscal aplicável: ausência ou não aplicação "
                "não é custo zero calculado."
            ),
        }
    if version.implementation_start is None or version.implementation_end is None:
        return {**base, "reason": "O período da proposta não foi informado."}
    reason = comparability(version.impacts)
    if reason:
        return {**base, "reason": reason}
    if any(
        not version.implementation_start <= row.year <= version.implementation_end
        for row in version.impacts
    ):
        return {**base, "reason": "Há parcelas fora do período publicado."}
    variants = [
        (
            "lower",
            "Saldo menor nas premissas escolhidas",
            assumptions.cost_high,
            assumptions.gain_low,
        ),
        ("declared", "Valores declarados", Decimal("1.00"), Decimal("1.00")),
        (
            "upper",
            "Saldo maior nas premissas escolhidas",
            assumptions.cost_low,
            assumptions.gain_high,
        ),
    ]
    scenarios = []
    with localcontext() as context:
        context.prec = 40
        for key, label, cost, gain in variants:
            entries = []
            for row in version.impacts:
                multiplier = (
                    cost if row.impact_type in {"NEW_EXPENSE", "REVENUE_REDUCTION"} else gain
                )
                amount = (row.amount * multiplier).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                if amount > MONEY_LIMIT:
                    return {
                        **base,
                        "reason": "As premissas ultrapassam o limite monetário do motor.",
                    }
                entries.append(Impact(row.year, ImpactType(row.impact_type), amount))
            result = simulate(
                version.implementation_start,
                version.implementation_end,
                (PolicyInput(str(version.id), EstimateStatus.ESTIMATED, tuple(entries)),),
            )
            scenarios.append(
                {
                    "key": key,
                    "label": label,
                    "cumulative_impact": str(result.cumulative_impact),
                    "years": [
                        {"year": row.year, "net_impact": str(row.net_impact)}
                        for row in result.years
                    ],
                }
            )
    return {**base, "available": True, "scenarios": scenarios}
