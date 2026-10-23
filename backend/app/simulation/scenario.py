"""Manual future primary accounts, isolated from HTTP, persistence and historical execution.

The first contract supports at most 30 future full years of Government Central cash
accounts in nominal BRL. Every amount is a human premise, never an extrapolation.
The historical snapshot establishes provenance and the starting year only: its
amounts are not copied, indexed, or added to the future premises.
"""

from dataclasses import dataclass
from decimal import Decimal, localcontext
from enum import StrEnum
from urllib.parse import urlsplit

from app.simulation.compatibility import EXPECTED, METADATA_FIELDS, valid_baseline
from app.simulation.fiscal import (
    EstimateStatus,
    Impact,
    ImpactType,
    PolicyInput,
    YearResult,
    simulate,
)

SCENARIO_METHOD_VERSION = "1.0.0"
MAX_HORIZON_YEARS = 30
MAX_MONEY = Decimal("9999999999999999.99")
METADATA_DOMAINS = {
    "fiscal_scope": {
        "CENTRAL_GOVERNMENT",
        "GENERAL_GOVERNMENT",
        "STATE",
        "MUNICIPAL",
        "OTHER",
        "UNSPECIFIED",
    },
    "accounting_basis": {"CASH", "ACCRUAL", "UNSPECIFIED"},
    "price_basis": {"NOMINAL", "CONSTANT", "UNSPECIFIED"},
    "component": {"PRIMARY", "INTEREST", "UNSPECIFIED"},
    "period_basis": {"FULL_YEAR", "PARTIAL_YEAR", "UNSPECIFIED"},
}
LIMITATIONS = (
    "Receitas e despesas futuras são premissas declaradas, não observações ou previsão oficial.",
    "Compatibilidade de recorte não valida custo, causalidade ou viabilidade das medidas.",
    "A exclusão prévia dos impactos é declaração do autor; não há detector de dupla contagem.",
    "Não há conversão de preços, indexação implícita, PIB, dívida, juros "
    "ou efeitos comportamentais.",
    "O acumulado apresentado soma apenas incrementais; não soma orçamentos anuais do cenário.",
)


class ScenarioStatus(StrEnum):
    COMPATIBLE = "COMPATIBLE"
    NOT_COMPARABLE = "NOT_COMPARABLE"
    INCOMPLETE = "INCOMPLETE"
    NO_IMPACTS = "NO_IMPACTS"


def _text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} deve ser texto não vazio.")


def _year(value, field="year"):
    if type(value) is not int or not 1900 <= value <= 2200:
        raise ValueError(f"{field} deve ser inteiro entre 1900 e 2200.")


def _money(value, field):
    if not isinstance(value, Decimal):
        raise ValueError(f"{field} deve ser Decimal, nunca float ou bool.")
    if not value.is_finite() or value < 0 or value > MAX_MONEY:
        raise ValueError(f"{field} deve ser finito, não negativo e caber em NUMERIC(18,2).")
    if value.as_tuple().exponent < -2:
        raise ValueError(f"{field} deve ter no máximo duas casas decimais.")


def _bool(value, field):
    if type(value) is not bool:
        raise ValueError(f"{field} deve ser bool explícito.")


def _urls(values):
    if not isinstance(values, tuple):
        raise ValueError("source_urls deve ser tupla imutável.")
    for value in values:
        _text(value, "source_url")
        if any(character.isspace() or ord(character) < 32 for character in value):
            raise ValueError("source_url não pode conter espaços ou controles.")
        try:
            parsed = urlsplit(value)
            valid = parsed.scheme in {"http", "https"} and bool(parsed.hostname)
            # Read port to reject malformed numeric/range values without any network call.
            _ = parsed.port
            valid = valid and parsed.username is None and parsed.password is None
        except ValueError as error:
            raise ValueError("source_url deve ser uma URL HTTP/HTTPS válida.") from error
        if not valid:
            raise ValueError("source_url deve ser HTTP/HTTPS, com host e sem credenciais.")


@dataclass(frozen=True)
class ScenarioYear:
    """One complete future year, including an explicit justification and optional references."""

    year: int
    net_revenue: Decimal
    primary_expenditure: Decimal
    justification: str
    source_urls: tuple[str, ...] = ()

    def __post_init__(self):
        _year(self.year)
        _money(self.net_revenue, "net_revenue")
        _money(self.primary_expenditure, "primary_expenditure")
        _text(self.justification, "justification")
        _urls(self.source_urls)


@dataclass(frozen=True)
class FiscalScenario:
    """Declared future accounts; excludes_plan_impacts never defaults to confirmation."""

    id: str
    title: str
    explanation: str
    reference_baseline_id: str
    start_year: int
    end_year: int
    years: tuple[ScenarioYear, ...]
    excludes_plan_impacts: bool = False
    fiscal_scope: str = "CENTRAL_GOVERNMENT"
    accounting_basis: str = "CASH"
    price_basis: str = "NOMINAL"
    price_base_year: int | None = None
    component: str = "PRIMARY"
    period_basis: str = "FULL_YEAR"
    currency: str = "BRL"

    def __post_init__(self):
        for field in ("id", "title", "explanation", "reference_baseline_id"):
            _text(getattr(self, field), field)
        _year(self.start_year, "start_year")
        _year(self.end_year, "end_year")
        if self.start_year > self.end_year:
            raise ValueError("O período do cenário está invertido.")
        if self.end_year - self.start_year + 1 > MAX_HORIZON_YEARS:
            raise ValueError("O cenário deve ter no máximo 30 anos.")
        if not isinstance(self.years, tuple) or any(
            not isinstance(row, ScenarioYear) for row in self.years
        ):
            raise ValueError("years deve ser tupla imutável de ScenarioYear.")
        observed = [row.year for row in self.years]
        expected = set(range(self.start_year, self.end_year + 1))
        if len(observed) != len(set(observed)) or set(observed) != expected:
            raise ValueError("Declare exatamente uma linha por ano do cenário, sem lacunas.")
        _bool(self.excludes_plan_impacts, "excludes_plan_impacts")
        if any(getattr(self, field) != expected for field, expected in EXPECTED.items()):
            raise ValueError(
                "O cenário exige Governo Central, caixa, nominal, primário e ano completo."
            )
        if self.currency != "BRL" or self.price_base_year is not None:
            raise ValueError("O cenário aceita apenas BRL nominal, sem ano-base de preços.")


@dataclass(frozen=True)
class ScenarioImpact:
    """A declared policy amount; absent metadata remains UNSPECIFIED."""

    id: str
    year: int
    kind: ImpactType
    amount: Decimal
    fiscal_scope: str = "UNSPECIFIED"
    accounting_basis: str = "UNSPECIFIED"
    price_basis: str = "UNSPECIFIED"
    price_base_year: int | None = None
    component: str = "UNSPECIFIED"
    period_basis: str = "UNSPECIFIED"

    def __post_init__(self):
        _text(self.id, "impact_id")
        _year(self.year)
        _money(self.amount, "amount")
        if not isinstance(self.kind, ImpactType):
            raise ValueError("kind deve ser ImpactType válido.")
        for field, choices in METADATA_DOMAINS.items():
            value = getattr(self, field)
            if not isinstance(value, str) or value not in choices:
                raise ValueError(f"{field} tem valor desconhecido.")
        if self.price_basis == "CONSTANT":
            _year(self.price_base_year, "price_base_year")
        elif self.price_base_year is not None:
            raise ValueError("price_base_year só se aplica a preços constantes.")


@dataclass(frozen=True)
class ScenarioPolicy:
    version_id: str
    status: EstimateStatus
    impacts: tuple[ScenarioImpact, ...] = ()
    enabled: bool = True
    unfunded: bool = False

    def __post_init__(self):
        _text(self.version_id, "policy_version_id")
        if not isinstance(self.status, EstimateStatus):
            raise ValueError("status deve ser EstimateStatus válido.")
        if not isinstance(self.impacts, tuple) or any(
            not isinstance(row, ScenarioImpact) for row in self.impacts
        ):
            raise ValueError("impacts deve ser tupla imutável de ScenarioImpact.")
        _bool(self.enabled, "enabled")
        _bool(self.unfunded, "unfunded")
        if self.status != EstimateStatus.ESTIMATED and self.impacts:
            raise ValueError("Somente proposta estimada pode declarar parcelas monetárias.")


@dataclass(frozen=True)
class ScenarioIssue:
    code: str
    field: str
    message: str
    policy_version_id: str | None = None
    impact_id: str | None = None
    year: int | None = None


@dataclass(frozen=True)
class ImpactAssessment:
    impact_id: str
    policy_version_id: str
    year: int
    status: ScenarioStatus
    issues: tuple[ScenarioIssue, ...]


@dataclass(frozen=True)
class ScenarioWarning:
    code: str
    message: str
    policy_version_id: str | None = None


@dataclass(frozen=True)
class PrimaryAccounts:
    net_revenue: Decimal
    primary_expenditure: Decimal
    primary_balance: Decimal


@dataclass(frozen=True)
class ScenarioYearResult:
    year: int
    declared: PrimaryAccounts
    incremental: YearResult
    combined: PrimaryAccounts | None


@dataclass(frozen=True)
class ScenarioResult:
    scenario: FiscalScenario
    historical_year: int
    status: ScenarioStatus
    years: tuple[ScenarioYearResult, ...]
    impacts: tuple[ImpactAssessment, ...]
    issues: tuple[ScenarioIssue, ...]
    warnings: tuple[ScenarioWarning, ...]
    cumulative_incremental: Decimal
    incremental_is_partial: bool
    aggregate_basis: str
    price_basis: str
    scenario_method_version: str
    aggregation_engine_version: str
    limitations: tuple[str, ...] = LIMITATIONS


def simulate_scenario(
    baseline_snapshot, scenario: FiscalScenario, policies: tuple[ScenarioPolicy, ...]
) -> ScenarioResult:
    """Review and combine only explicitly compatible, excluded-from-premises policy amounts.

    Any active incompatibility, missing estimate, unchecked double counting or negative
    projected revenue/expenditure blocks combination in *all* years. Declared premises
    and the original arithmetic incremental are still returned separately. Inputs and
    the historical snapshot remain unchanged, and no sources are fetched.
    """
    if not isinstance(scenario, FiscalScenario):
        raise ValueError("scenario deve ser FiscalScenario.")
    if not isinstance(policies, tuple) or any(
        not isinstance(policy, ScenarioPolicy) for policy in policies
    ):
        raise ValueError("policies deve ser tupla imutável de ScenarioPolicy.")
    # The historical validator also operates under an explicit precision, never caller rounding.
    with localcontext() as context:
        context.prec = 40
        historical = valid_baseline(baseline_snapshot)
    if historical is None:
        raise ValueError("A referência histórica deve ser RTN completo e compatível verificado.")
    baseline_id = baseline_snapshot.get("id")
    _text(baseline_id, "baseline_snapshot.id")
    if scenario.reference_baseline_id != baseline_id:
        raise ValueError("reference_baseline_id difere do snapshot histórico fornecido.")
    if scenario.start_year <= historical["year"]:
        raise ValueError("Todos os anos do cenário devem ser posteriores ao ano histórico.")
    policy_ids = [policy.version_id for policy in policies]
    impact_ids = [row.id for policy in policies for row in policy.impacts]
    if len(policy_ids) != len(set(policy_ids)):
        raise ValueError("Uma versão de proposta não pode aparecer duas vezes.")
    if len(impact_ids) != len(set(impact_ids)):
        raise ValueError("Identificadores de parcelas não podem se repetir.")
    issues = []
    assessments = []
    included = []
    extra_warnings = []
    engine_inputs = []
    # Constructors of the legacy pure motor quantize Decimal; isolate caller precision as well.
    with localcontext() as context:
        context.prec = 40
        for policy in policies:
            engine_inputs.append(
                PolicyInput(
                    policy.version_id,
                    policy.status,
                    tuple(Impact(row.year, row.kind, row.amount) for row in policy.impacts),
                    enabled=policy.enabled,
                    unfunded=policy.unfunded,
                )
            )
            if not policy.enabled:
                extra_warnings.append(
                    ScenarioWarning(
                        "POLICY_DISABLED",
                        "Proposta desativada não entra na combinação.",
                        policy.version_id,
                    )
                )
                continue
            if policy.status == EstimateStatus.NOT_ESTIMATED:
                issues.append(
                    ScenarioIssue(
                        "NOT_ESTIMATED",
                        "status",
                        "Uma proposta ativa não tem estimativa; a combinação não é completa.",
                        policy.version_id,
                    )
                )
            for row in policy.impacts:
                if not scenario.start_year <= row.year <= scenario.end_year:
                    continue
                included.append(row)
                reasons = []
                mismatch = False
                incomplete = False
                for field, expected in EXPECTED.items():
                    value = getattr(row, field)
                    if value == "UNSPECIFIED":
                        incomplete = True
                        reasons.append(
                            ScenarioIssue(
                                "METADATA_UNSPECIFIED",
                                field,
                                "Informe o recorte fiscal desta parcela.",
                                policy.version_id,
                                row.id,
                                row.year,
                            )
                        )
                    elif value != expected:
                        mismatch = True
                        reasons.append(
                            ScenarioIssue(
                                "METADATA_DIFFERS",
                                field,
                                "O recorte declarado difere do cenário nominal do Governo Central.",
                                policy.version_id,
                                row.id,
                                row.year,
                            )
                        )
                row_status = (
                    ScenarioStatus.NOT_COMPARABLE
                    if mismatch
                    else ScenarioStatus.INCOMPLETE
                    if incomplete
                    else ScenarioStatus.COMPATIBLE
                )
                assessments.append(
                    ImpactAssessment(
                        row.id, policy.version_id, row.year, row_status, tuple(reasons)
                    )
                )
        arithmetic = simulate(scenario.start_year, scenario.end_year, tuple(engine_inputs))
    warnings = [
        ScenarioWarning(
            warning.code, "Aviso do somatório incremental declarado.", warning.policy_version_id
        )
        for warning in arithmetic.warnings
    ]
    warnings.extend(extra_warnings)
    signatures = {tuple(getattr(row, field) for field in METADATA_FIELDS) for row in included}
    missing = any(
        any(getattr(row, field) == "UNSPECIFIED" for field in EXPECTED) for row in included
    )
    aggregate_basis = (
        "UNSPECIFIED"
        if missing or not included
        else "MIXED"
        if len(signatures) > 1
        else "HOMOGENEOUS"
    )
    price_keys = {(row.price_basis, row.price_base_year) for row in included}
    price_basis = (
        "UNSPECIFIED"
        if not price_keys or any(key[0] == "UNSPECIFIED" for key in price_keys)
        else "MIXED"
        if len(price_keys) > 1
        else next(iter(price_keys))[0]
    )
    if missing:
        warnings.append(
            ScenarioWarning(
                "FISCAL_METADATA_MISSING",
                "Há parcelas sem recorte fiscal completo; o incremental é apenas soma declarada.",
            )
        )
    if len(signatures) > 1:
        warnings.append(
            ScenarioWarning(
                "FISCAL_AGGREGATE_HETEROGENEOUS",
                "O incremental mistura recortes; não representa uma conta fiscal homogênea.",
            )
        )
    if assessments and not scenario.excludes_plan_impacts:
        issues.append(
            ScenarioIssue(
                "DOUBLE_COUNTING_UNCHECKED",
                "excludes_plan_impacts",
                "O autor deve declarar que as premissas anuais excluem as medidas selecionadas.",
            )
        )
        warnings.append(
            ScenarioWarning(
                "DOUBLE_COUNTING_UNCHECKED",
                "A exclusão prévia das medidas nas premissas não foi declarada.",
            )
        )
    if any(row.status == ScenarioStatus.NOT_COMPARABLE for row in assessments) or any(
        issue.code == "DOUBLE_COUNTING_UNCHECKED" for issue in issues
    ):
        status = ScenarioStatus.NOT_COMPARABLE
    elif arithmetic.is_partial or any(
        row.status == ScenarioStatus.INCOMPLETE for row in assessments
    ):
        status = ScenarioStatus.INCOMPLETE
    elif not assessments:
        status = ScenarioStatus.NO_IMPACTS
    else:
        status = ScenarioStatus.COMPATIBLE
    declared_by_year = {row.year: row for row in scenario.years}
    combined_by_year = {}
    with localcontext() as context:
        context.prec = 40
        if status == ScenarioStatus.COMPATIBLE:
            for incremental in arithmetic.years:
                declared = declared_by_year[incremental.year]
                revenue = (
                    declared.net_revenue + incremental.new_revenues - incremental.revenue_reductions
                )
                expenditure = (
                    declared.primary_expenditure
                    + incremental.new_expenses
                    - incremental.expense_reductions
                )
                for field, value in (
                    ("net_revenue", revenue),
                    ("primary_expenditure", expenditure),
                ):
                    if value < 0:
                        issues.append(
                            ScenarioIssue(
                                "NEGATIVE_PROJECTED_COMPONENT",
                                field,
                                "A combinação produziria um componente negativo; "
                                "revise as premissas e medidas.",
                                year=incremental.year,
                            )
                        )
                    elif value > MAX_MONEY:
                        issues.append(
                            ScenarioIssue(
                                "PROJECTED_AMOUNT_OVERFLOW",
                                field,
                                "O componente combinado excede NUMERIC(18,2); "
                                "os valores separados foram preservados.",
                                year=incremental.year,
                            )
                        )
                combined_by_year[incremental.year] = PrimaryAccounts(
                    revenue, expenditure, revenue - expenditure
                )
            if issues:
                status = ScenarioStatus.NOT_COMPARABLE
                combined_by_year.clear()
                for code in sorted({issue.code for issue in issues}):
                    warnings.append(
                        ScenarioWarning(
                            code,
                            "A combinação foi bloqueada em todos os anos; "
                            "não houve ajuste, descarte ou truncamento de valores.",
                        )
                    )
        years = tuple(
            ScenarioYearResult(
                row.year,
                PrimaryAccounts(
                    declared_by_year[row.year].net_revenue,
                    declared_by_year[row.year].primary_expenditure,
                    declared_by_year[row.year].net_revenue
                    - declared_by_year[row.year].primary_expenditure,
                ),
                row,
                combined_by_year.get(row.year),
            )
            for row in arithmetic.years
        )
    return ScenarioResult(
        scenario,
        historical["year"],
        status,
        years,
        tuple(assessments),
        tuple(issues),
        tuple(warnings),
        arithmetic.cumulative_impact,
        arithmetic.is_partial,
        aggregate_basis,
        price_basis,
        SCENARIO_METHOD_VERSION,
        arithmetic.engine_version,
    )
