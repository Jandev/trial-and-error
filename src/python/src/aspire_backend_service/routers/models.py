from typing import Any

from pydantic import BaseModel, Field


# JSON-RPC 2.0 models
class JsonRpcRequest(BaseModel):
    jsonrpc: str = Field(default="2.0")
    method: str | None = None
    params: Any | None = None
    id: int | str | None = None


class JsonRpcResponse(BaseModel):
    jsonrpc: str = Field(default="2.0")
    result: Any
    id: int | str | None = None


class JsonRpcError(BaseModel):
    code: int
    message: str
    data: Any | None = None


class JsonRpcErrorResponse(BaseModel):
    jsonrpc: str = Field(default="2.0")
    error: JsonRpcError
    id: int | str | None = None


# A2A Protocol Models - Request/Response structures
class A2AMessagePart(BaseModel):
    """A2A Message Part - represents content within a message"""

    kind: str
    text: str


class A2AMessage(BaseModel):
    """A2A Message - the core message structure"""

    kind: str = "message"
    role: str
    parts: list[A2AMessagePart]
    messageId: str


class A2ASendMessageParams(BaseModel):
    """A2A SendMessage parameters"""

    message: A2AMessage


class A2AJsonRpcRequest(BaseModel):
    """A2A JSON-RPC request with typed params"""

    jsonrpc: str = "2.0"
    method: str
    params: A2ASendMessageParams
    id: str | int


# A2A Protocol Models - Agent Card structures
class AgentCapabilities(BaseModel):
    streaming: bool = Field(default=False)
    pushNotifications: bool = Field(default=False, alias="push_notifications")

    class Config:
        populate_by_name = True


class AgentInterface(BaseModel):
    url: str
    protocolBinding: str = Field(alias="protocol_binding")
    protocolVersion: str = Field(alias="protocol_version")

    class Config:
        populate_by_name = True


class AgentSkill(BaseModel):
    id: str
    name: str
    description: str
    tags: list[str]
    examples: list[str]


class AgentCard(BaseModel):
    name: str
    description: str
    version: str
    # Support both old and new A2A protocol versions
    # Old format (for backward compatibility with .NET client)
    url: str
    protocolVersion: str = Field(alias="protocol_version")
    preferredTransport: str = Field(default="HTTP", alias="preferred_transport")
    # New format (A2A v1.0 spec)
    supportedInterfaces: list[AgentInterface] = Field(alias="supported_interfaces")
    defaultInputModes: list[str] = Field(alias="default_input_modes")
    defaultOutputModes: list[str] = Field(alias="default_output_modes")
    capabilities: AgentCapabilities
    skills: list[AgentSkill]

    class Config:
        populate_by_name = True
        # Use the field name (camelCase) for serialization, not the alias
        by_alias = False


class CountLettersResponse(BaseModel):
    finalNumber: float
    reasoning: str
    chainOfThought: str
    answer: str


class LargeDataAnalysisResponse(BaseModel):
    summary: str
    analysisResults: dict = Field(alias="analysis_results")
    insights: list[str]
    algorithmUsed: str = Field(alias="algorithm_used")

    class Config:
        populate_by_name = True
