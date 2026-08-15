import uuid
from datetime import datetime

from pydantic import BaseModel, Field

class AgentCreate(BaseModel):
    name: str = Field(min_length =1,max_length=100)
    description: str | None = None

class AgentResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    status: str
    
    model_config = {
            "from_attributes": True
    }

class ProfileCreate(BaseModel):
    agent_id: uuid.UUID
    name: str = Field(min_length=1,max_length=100)

    allowed_tools: list[str] = Field(default_factory=list)
    allowed_data_sources: list[str] = Field(default_factory=list)
    allowed_actions: list[str] = Field(default_factory=list)

    max_llm_calls: int = Field(
            default=1000,
            gt=0
    )

    warning_threshold: int = Field(
            default=80,
            ge=1,
            le=100
    )

    critical_threshold: int = Field(
            default=90,
            ge=1,
            le=100
    )

class ProfileResponse(BaseModel):
    id: uuid.UUID
    agent_id: uuid.UUID
    name: str

    allowed_tools: list[str]
    allowed_data_sources: list[str]
    allowed_actions: list[str]

    max_llm_calls: int
    warning_threshold: int
    critical_threshold: int

    model_config = {
            "from_attributes": True
    }


class ApprovalDecisionRequest(BaseModel):
    approved: bool
    decided_by: str = Field(min_length=1, max_length=100)
    reason: str = Field(min_length=1, max_length=1000)

class RunCreate(BaseModel):
    agent_id: uuid.UUID

class AgentRunRequest(BaseModel):
    agent_id: uuid.UUID
    message: str = Field(min_length=1, max_length=2000)


class RunResponse(BaseModel):
    id: uuid.UUID
    agent_id: uuid.UUID
    status: str

    model_config = {
        "from_attributes": True
    }

class FindingResponse(BaseModel):
    id: uuid.UUID
    agent_id: uuid.UUID
    run_id: uuid.UUID
    finding_type: str
    severity: str
    expected: str
    actual: str
    reason: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}

class ApprovalResponse(BaseModel):
    id: uuid.UUID
    finding_id: uuid.UUID
    status: str
    requested_by: str
    decided_by: str | None
    decision_reason: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class EventCreate(BaseModel):
    event_type: str
    tool_name: str | None = None
    status: str
    details: dict = {}


class EventResponse(BaseModel):
    id: uuid.UUID
    run_id: uuid.UUID
    agent_id: uuid.UUID
    event_type: str
    tool_name: str | None
    status: str
    details: dict

    model_config = {
        "from_attributes": True
    }
    
class AgentDecisionRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=5000,
    )


class AgentDecisionResponse(BaseModel):
    tool_name: str
    arguments: dict
    source: str
