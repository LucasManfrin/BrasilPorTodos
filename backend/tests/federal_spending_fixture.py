"""Invented twelve-month aggregates for persistence tests; never real federal data."""

from copy import deepcopy
from decimal import Decimal
from hashlib import sha256

from app.integrations import federal_spending as provider


def payload(year=2025, paid="100.10", rap="10.01", tag="synthetic-file-one"):
    paid, rap = Decimal(paid), Decimal(rap)
    values = {"PAID": paid, "RAP_PAID": rap, "TOTAL_PAID": paid + rap}
    monthly = {stage: format(value, ".2f") for stage, value in values.items()}
    annual = {stage: format(value * 12, ".2f") for stage, value in values.items()}
    identity = {
        "nature": "PRIMARY",
        "nature_label": provider.NATURES["PRIMARY"],
        "function_key": "FUNCTION_10",
        "function_code": "10",
        "source_function_code": "10",
        "function_label": "SAUDE",
        "classification": "BUDGET_FUNCTION",
    }
    resource_id = "f40d5431-058d-48b8-9ab6-065fb0fce5b3"
    resource = {
        "id": resource_id,
        "url": f"https://www.tesourotransparente.gov.br/ckan/dataset/{provider.DATASET_ID}"
        f"/resource/{resource_id}/download/synthetic-{year}.xlsx",
        "last_modified": "2026-01-01T00:00:00",
        "size": 1024,
        "sha256": sha256(tag.encode()).hexdigest(),
    }
    result = {
        "year": year,
        "scope": provider.SCOPE,
        "currency": "BRL",
        "price_basis": "CURRENT",
        "accounting_basis": "OB_ISSUANCE_VALUE_PAID",
        "periodicity": "MONTHLY_MOVEMENT",
        "parser_version": provider.PARSER_VERSION,
        "precision_version": provider.PRECISION_VERSION,
        "source": deepcopy(provider.SOURCE),
        "resource": resource,
        "row_count": 12,
        "stages": list(provider.STAGES),
        "totals": annual,
        "months": [
            {
                "month": month,
                "row_count": 1,
                "totals": deepcopy(monthly),
                "groups": [{**identity, "row_count": 1, "amounts": deepcopy(monthly)}],
            }
            for month in range(1, 13)
        ],
        "functions": [
            {
                **identity,
                "row_count": 12,
                "amounts": deepcopy(annual),
                "observed_months": list(range(1, 13)),
            }
        ],
        "natures": [
            {
                "nature": "PRIMARY",
                "nature_label": provider.NATURES["PRIMARY"],
                "row_count": 12,
                "amounts": deepcopy(annual),
                "observed_months": list(range(1, 13)),
            }
        ],
        "absence_policy": provider.ABSENCE_POLICY,
        "reconciliation": {
            "row_payment_difference_max": "0.00",
            "group_total_differences": dict.fromkeys(provider.STAGES, "0.00"),
            "raw_minus_rounded_totals": dict.fromkeys(provider.STAGES, "0.000"),
            "published_subset": {
                "labels": ["1.1 - Categoria fictícia para teste"],
                "scope": provider.SUBSET_SCOPE,
                "months": [
                    {
                        "month": month,
                        "published_total": monthly["TOTAL_PAID"],
                        "calculated_total": monthly["TOTAL_PAID"],
                        "difference": "0.00",
                    }
                    for month in range(1, 13)
                ],
                "annual_published_total": annual["TOTAL_PAID"],
                "annual_calculated_total": annual["TOTAL_PAID"],
                "annual_difference": "0.00",
            },
        },
    }
    result["fingerprint"] = provider.fingerprint(result)
    provider.validate_payload(result)
    return result
