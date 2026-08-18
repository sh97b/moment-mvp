from pydantic import BaseModel, ConfigDict


class ScenarioSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    description: str


class ScenarioListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenarios: list[ScenarioSummary]
