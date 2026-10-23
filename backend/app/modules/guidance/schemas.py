from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.guidance.script import SCRIPT


class OrganizeInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    step_id: str = Field(max_length=40)
    answer: str = Field(min_length=1, max_length=4000)
    consent: bool = False
    use_ai: bool = True
    context: dict[str, str] = Field(default_factory=dict, max_length=8)

    @field_validator("context")
    @classmethod
    def confirmed_text_context(cls, value):
        allowed = {step["field"] for step in SCRIPT["steps"]}
        if set(value) - allowed or sum(len(text) for text in value.values()) > 12000:
            raise ValueError(
                "Contexto deve conter somente campos do roteiro, até 12000 caracteres."
            )
        return value

    @field_validator("step_id")
    @classmethod
    def known_step(cls, value):
        if value not in {step["id"] for step in SCRIPT["steps"]}:
            raise ValueError("Etapa desconhecida.")
        return value
