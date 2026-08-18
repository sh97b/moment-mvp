"""시나리오 목록 API의 공개 응답 모델."""

from pydantic import BaseModel, ConfigDict


class ScenarioSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    description: str


class ScenarioListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenarios: list[ScenarioSummary]
