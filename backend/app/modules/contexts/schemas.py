"""HTTP inputs contain content references, never trusted identities or approval."""

import json
from typing import Annotated
from uuid import UUID

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    StrictBool,
    StrictInt,
    StringConstraints,
    model_validator,
)

from app.modules.contexts.context import (
    Consequence,
    Counterpart,
    Evidence,
    Hypothesis,
    ReviewDecision,
    Text,
)


def nested_contract(model):
    def validate(value):
        if isinstance(value, model):
            return model.model_validate(value)
        # JSON transport allows UUID/enum strings while retaining strict numeric/boolean rules.
        try:
            return model.model_validate_json(json.dumps(value))
        except (TypeError, ValueError) as error:
            raise ValueError("Conteúdo estruturado inválido.") from error

    return BeforeValidator(validate)


class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ContextContentInput(InputModel):
    title: Annotated[str, StringConstraints(strict=True, max_length=180)] = ""
    observation_summary: Annotated[str, StringConstraints(strict=True, max_length=4000)] = ""
    primary_observation_id: UUID | None = None
    observation_ids: Annotated[tuple[UUID, ...], Field(max_length=64)] = ()
    source_ids: Annotated[tuple[UUID, ...], Field(max_length=64)] = ()
    counterparts: Annotated[
        tuple[Annotated[Counterpart, nested_contract(Counterpart)], ...], Field(max_length=32)
    ] = ()
    evidence: Annotated[
        tuple[Annotated[Evidence, nested_contract(Evidence)], ...], Field(max_length=64)
    ] = ()
    hypotheses: Annotated[
        tuple[Annotated[Hypothesis, nested_contract(Hypothesis)], ...], Field(max_length=16)
    ] = ()
    consequences: Annotated[
        tuple[Annotated[Consequence, nested_contract(Consequence)], ...], Field(max_length=32)
    ] = ()
    limitations: Annotated[tuple[Text, ...], Field(max_length=32)] = ()
    unknowns: Annotated[tuple[Text, ...], Field(max_length=32)] = ()

    @model_validator(mode="after")
    def unique_ids(self):
        if len(set(self.observation_ids)) != len(self.observation_ids) or len(
            set(self.source_ids)
        ) != len(self.source_ids):
            raise ValueError("Referência duplicada.")
        if (
            self.primary_observation_id is not None
            and self.primary_observation_id not in self.observation_ids
        ):
            raise ValueError("Observação principal ausente do conjunto.")
        return self


class ContextCreate(InputModel):
    content: ContextContentInput


class ContextUpdate(ContextCreate):
    expected_revision: Annotated[StrictInt, Field(ge=1, le=2147483647)]


class ContextReviewInput(InputModel):
    expected_revision: Annotated[StrictInt, Field(ge=1, le=2147483647)]
    decision: ReviewDecision
    rationale: Text
    references_checked: StrictBool
    scopes_checked: StrictBool
    alternatives_checked: StrictBool
    limitations_checked: StrictBool


class ContextPublishInput(InputModel):
    expected_revision: Annotated[StrictInt, Field(ge=1, le=2147483647)]
