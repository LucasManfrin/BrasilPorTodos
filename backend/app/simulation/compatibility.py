"""Versioned review of declared fiscal metadata; never extrapolates or adds a baseline."""

from collections import Counter
from decimal import Decimal, InvalidOperation

VERSION = "1.0.0"
METADATA_FIELDS = (
    "fiscal_scope",
    "accounting_basis",
    "price_basis",
    "price_base_year",
    "component",
    "period_basis",
)
CENTRAL_SCOPE = (
    "Governo Central: Tesouro Nacional, Previdência Social e Banco Central; "
    "exclui estados e municípios"
)
EXPECTED = {
    "fiscal_scope": "CENTRAL_GOVERNMENT",
    "accounting_basis": "CASH",
    "price_basis": "NOMINAL",
    "component": "PRIMARY",
    "period_basis": "FULL_YEAR",
}
FIELD_LABELS = {
    "fiscal_scope": "ente fiscal",
    "accounting_basis": "critério contábil",
    "price_basis": "base de preços",
    "component": "componente fiscal",
    "period_basis": "cobertura do ano",
}


def issue(code, field, message):
    return {"code": code, "field": field, "message": message}


def valid_baseline(baseline):
    """Only the reviewed frozen RTN contract; similar free text is not accepted."""
    fiscal = baseline.get("fiscal") if isinstance(baseline, dict) else None
    if not isinstance(fiscal, dict):
        return None
    year = fiscal.get("year")
    if (
        fiscal.get("status") != "AVAILABLE"
        or type(year) is not int
        or not 1900 <= year <= 2200
        or fiscal.get("scope") != CENTRAL_SCOPE
        or fiscal.get("accounting_basis") != "cash"
        or fiscal.get("price_basis") != "nominal"
        or fiscal.get("currency") != "BRL"
        or fiscal.get("period_start") != f"{year}-01-01"
        or fiscal.get("period_end") != f"{year}-12-31"
    ):
        return None
    months = fiscal.get("months", [])
    if (
        not isinstance(months, list)
        or len(months) != 12
        or {row.get("reference_date") for row in months if isinstance(row, dict)}
        != {f"{year}-{month:02d}-01" for month in range(1, 13)}
    ):
        return None
    source = fiscal.get("source")
    if not isinstance(source, dict) or source.get("url") != (
        "https://www.tesourotransparente.gov.br/ckan/dataset/resultado-do-tesouro-nacional"
    ):
        return None
    amounts = fiscal.get("amounts")
    if not isinstance(amounts, dict):
        return None
    try:
        values = {
            field: Decimal(amounts[field])
            for field in (
                "net_revenue",
                "primary_expenditure",
                "published_primary_balance",
                "calculated_primary_balance",
                "reconciliation_difference",
            )
        }
        if (
            not all(value.is_finite() for value in values.values())
            or values["net_revenue"] < 0
            or values["primary_expenditure"] < 0
        ):
            return None
        if (
            values["net_revenue"] - values["primary_expenditure"]
            != values["calculated_primary_balance"]
            or values["calculated_primary_balance"] - values["published_primary_balance"]
            != values["reconciliation_difference"]
            or abs(values["reconciliation_difference"]) > Decimal("0.36")
        ):
            return None
    except (KeyError, TypeError, ValueError, InvalidOperation):
        return None
    return fiscal


def assess(baseline, policies, start_year, end_year):
    fiscal = valid_baseline(baseline)
    baseline_year = fiscal["year"] if fiscal else None
    top_issues = []
    evaluations = []
    metadata = []
    enabled = [p for p in policies if p["enabled"]]
    if any(p["estimate_status"] == "NOT_ESTIMATED" for p in enabled):
        top_issues.append(
            issue(
                "NOT_ESTIMATED",
                "estimate_status",
                "Há proposta ativa sem estimativa fiscal; a cobertura não é completa.",
            )
        )
    for policy in enabled:
        for impact in policy["impacts"]:
            if not start_year <= impact["year"] <= end_year:
                continue
            metadata.append(impact)
            reasons = []
            unknown = False
            mismatch = False
            if fiscal is None:
                mismatch = True
                reasons.append(
                    issue(
                        "BASELINE_UNAVAILABLE",
                        "baseline",
                        "A referência fiscal congelada não tem um ano completo "
                        "compatível verificado.",
                    )
                )
            elif impact["year"] != baseline_year:
                mismatch = True
                code = (
                    "FUTURE_ASSUMPTIONS_REQUIRED"
                    if impact["year"] > baseline_year
                    else "YEAR_DIFFERS"
                )
                reasons.append(
                    issue(
                        code,
                        "year",
                        "O ano do impacto difere do ano observado; anos futuros exigem "
                        "premissas de cenário ainda não modeladas.",
                    )
                )
            for field, expected in EXPECTED.items():
                value = impact.get(field, "UNSPECIFIED")
                if value == "UNSPECIFIED":
                    unknown = True
                    reasons.append(
                        issue(
                            "METADATA_UNSPECIFIED",
                            field,
                            f"Informe {FIELD_LABELS[field]} para avaliar a compatibilidade.",
                        )
                    )
                elif value != expected:
                    mismatch = True
                    reasons.append(
                        issue(
                            "METADATA_DIFFERS",
                            field,
                            f"O {FIELD_LABELS[field]} declarado difere da referência observada "
                            "do Governo Central.",
                        )
                    )
            # Unknown future enum values cannot accidentally become compatible.
            status = "NOT_COMPARABLE" if mismatch else "INCOMPLETE" if unknown else "COMPATIBLE"
            evaluations.append(
                {
                    "impact_id": impact["id"],
                    "policy_version_id": policy["version_id"],
                    "year": impact["year"],
                    "status": status,
                    "issues": reasons,
                }
            )
    signatures = {
        tuple(
            row.get(f, None if f == "price_base_year" else "UNSPECIFIED") for f in METADATA_FIELDS
        )
        for row in metadata
    }
    if len(signatures) > 1:
        top_issues.append(
            issue(
                "AGGREGATE_HETEROGENEOUS",
                "metadata",
                "O total incremental reúne declarações fiscais diferentes; "
                "não deve ser interpretado como uma conta fiscal homogênea.",
            )
        )
    missing = any(
        any(row.get(f, "UNSPECIFIED") == "UNSPECIFIED" for f in EXPECTED) for row in metadata
    )
    if missing:
        top_issues.append(
            issue(
                "METADATA_UNSPECIFIED",
                "metadata",
                "Há impactos sem metadados fiscais completos; "
                "o total é apenas a soma dos valores declarados.",
            )
        )
    counts = Counter(row["status"] for row in evaluations)
    if not evaluations:
        status = "INCOMPLETE" if top_issues else "NO_IMPACTS"
    elif counts["NOT_COMPARABLE"]:
        status = "NOT_COMPARABLE"
    elif counts["INCOMPLETE"] or top_issues:
        status = "INCOMPLETE"
    else:
        status = "COMPATIBLE"
    price_keys = {
        (row.get("price_basis", "UNSPECIFIED"), row.get("price_base_year")) for row in metadata
    }
    price_basis = (
        "UNSPECIFIED"
        if not price_keys or any(key[0] == "UNSPECIFIED" for key in price_keys)
        else "MIXED"
        if len(price_keys) > 1
        else next(iter(price_keys))[0]
    )
    assessment = {
        "version": VERSION,
        "status": status,
        "baseline_year": baseline_year,
        "baseline_combined": False,
        "impacts": evaluations,
        "issues": top_issues,
        "coverage": {
            "considered": len(evaluations),
            "compatible": counts["COMPATIBLE"],
            "not_comparable": counts["NOT_COMPARABLE"],
            "incomplete": counts["INCOMPLETE"],
        },
    }
    interpretation = {
        "price_basis": price_basis,
        "price_base_year": next(iter(price_keys))[1] if price_basis == "CONSTANT" else None,
        "aggregate_basis": "UNSPECIFIED"
        if missing or not metadata
        else "MIXED"
        if len(signatures) > 1
        else "HOMOGENEOUS",
        "baseline_combined": False,
        "total_kind": "DECLARED_INCREMENTAL_SUM",
    }
    warnings = []
    if missing:
        warnings.append(
            {
                "code": "FISCAL_METADATA_MISSING",
                "message": (
                    "Parte dos impactos não informa ente, critério, preços, componente "
                    "ou cobertura anual. O total mantém apenas os valores declarados."
                ),
            }
        )
    if len(signatures) > 1:
        warnings.append(
            {
                "code": "FISCAL_AGGREGATE_HETEROGENEOUS",
                "message": (
                    "O total combina metadados fiscais diferentes. "
                    "Leia os impactos separadamente antes de interpretar essa soma."
                ),
            }
        )
    if status != "COMPATIBLE":
        warnings.append(
            {
                "code": "FISCAL_BASELINE_NOT_COMPARABLE",
                "message": (
                    "Os impactos não podem ser combinados com a referência fiscal observada. "
                    "Confira os motivos por impacto; cenários futuros ainda precisam "
                    "de premissas explícitas."
                ),
            }
        )
    return assessment, interpretation, warnings
