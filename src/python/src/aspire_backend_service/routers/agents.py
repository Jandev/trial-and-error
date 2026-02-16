import json
import logging
from typing import Any, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError

from ..agents.calculator import calculator
from ..agents.hello import hello
from .request_models import CountLettersRequest

logger = logging.getLogger(__name__)


# JSON-RPC 2.0 models
class JsonRpcRequest(BaseModel):
    jsonrpc: str = Field(default="2.0")
    method: Optional[str] = None
    params: Optional[Any] = None
    id: Optional[int | str] = None


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


router = APIRouter(
    prefix="/agents",
    tags=["agents"],
    responses={404: {"description": "Not Found"}},
)


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


class count_letters_response(BaseModel):
    finalNumber: float
    reasoning: str
    chainOfThought: str
    answer: str


@router.get("/hello-world")
async def hello_world():
    """
    This is a test method to validate if the application
    working and we get a response using the pattern of
    creating an object and invoking a method.
    """
    subject = hello()
    response_message = await subject.run()
    return {"message": response_message}


@router.post("/count-letters")
async def count_letters(request: CountLettersRequest) -> count_letters_response:
    """
    Regular REST API endpoint for counting letters.
    Accepts: {"question": "..."}
    Returns: count_letters_response
    """
    logger.info(f"Received count-letters request: {request.model_dump()}")
    logger.debug(f"Request question field: '{request.question}' (type: {type(request.question)})")

    subject = calculator()
    results = await subject.run(request.question)

    if results is None:
        logger.warning("Calculator returned None results")
        return count_letters_response(answer="", finalNumber=0, reasoning="", chainOfThought="")

    responseValue = count_letters_response(
        answer=results.answer,
        chainOfThought=results.chain_of_thought,
        reasoning=results.reasoning,
        finalNumber=results.final_number,
    )

    logger.info(f"Returning response: finalNumber={responseValue.finalNumber}")
    return responseValue


@router.post("/count-letters-a2a")
async def count_letters_a2a(request: A2AJsonRpcRequest) -> JSONResponse:
    """
    A2A JSON-RPC 2.0 endpoint for counting letters.
    Accepts A2A-compliant JSON-RPC request with typed message structure.
    Returns: JSON-RPC 2.0 response with A2A Message object
    """
    try:
        logger.info(
            f"A2A endpoint - Method: {request.method}, Message ID: {request.params.message.messageId}"
        )

        # Extract question from the first text part
        question = None
        for part in request.params.message.parts:
            if part.kind == "text":
                question = part.text
                break

        if not question:
            error_response = JsonRpcErrorResponse(
                error=JsonRpcError(
                    code=-32602,
                    message="Invalid A2A message - no text part found in message.parts",
                ),
                id=request.id,
            )
            return JSONResponse(content=error_response.model_dump(), status_code=400)

        logger.info(f"Extracted question: {question}")

        # Run the calculator
        subject = calculator()
        results = await subject.run(question)

        if results is None:
            logger.warning("Calculator returned None results")
            answer_text = "I couldn't process the question."
        else:
            # Format the answer as a text response combining all information
            answer_text = (
                f"Answer: {results.answer}\n"
                f"Final Number: {results.final_number}\n"
                f"Reasoning: {results.reasoning}\n"
                f"Chain of Thought: {results.chain_of_thought}"
            )

        # Generate UUID for response message
        import uuid

        message_id = str(uuid.uuid4())

        # According to A2A spec section 3.1.1, SendMessage can return either:
        # - A Task object (for async processing)
        # - A Message object (for simple synchronous interactions)
        #
        # Since we're doing synchronous processing, return a Message directly
        a2a_message = {
            "kind": "message",
            "messageId": message_id,
            "role": "Agent",  # .NET expects PascalCase role
            "parts": [{"kind": "text", "text": answer_text}],
        }

        # Return JSON-RPC response with A2A Message object
        jsonrpc_response = JsonRpcResponse(result=a2a_message, id=request.id)
        response_data = jsonrpc_response.model_dump()
        logger.info(
            f"Returning A2A-compliant JSON-RPC response with Message object: {json.dumps(response_data)}"
        )
        return JSONResponse(content=response_data)

    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        error_response = JsonRpcErrorResponse(
            error=JsonRpcError(code=-32600, message="Invalid Request", data=e.errors()),
            id=getattr(request, "id", None),
        )
        return JSONResponse(content=error_response.model_dump(), status_code=400)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        error_response = JsonRpcErrorResponse(
            error=JsonRpcError(code=-32603, message="Internal error", data=str(e)),
            id=getattr(request, "id", None),
        )
        return JSONResponse(content=error_response.model_dump(), status_code=500)


@router.get("/count-letters/.well-known/agent-card.json")
async def get_count_letters_agent_card(request: Request):
    """
    Returns the A2A protocol agent card for the count-letters agent.
    This endpoint provides agent discovery information following the A2A specification.
    """
    capabilities = AgentCapabilities(
        streaming=False,
        push_notifications=False,
    )

    count_letters_skill = AgentSkill(
        id="id_count_letters_agent",
        name="CountLettersAgent",
        description="Analyzes text to count letters and provide detailed reasoning about letter counts in questions.",
        tags=["calculator", "letter-counting", "text-analysis"],
        examples=[
            "How many letters are in the word 'hello'?",
            "Count the letters in this sentence",
            "What is the letter count of 'Python'?",
        ],
    )

    # Build the base URL from the request, respecting proxy headers
    # Azure Container Apps and other cloud platforms use reverse proxies
    scheme = request.headers.get("X-Forwarded-Proto", request.url.scheme)
    host = request.headers.get("X-Forwarded-Host", request.url.netloc)
    base_url = f"{scheme}://{host}"
    # Point to the A2A-specific endpoint that handles JSON-RPC
    agent_url = f"{base_url}/agents/count-letters-a2a"

    # Define supported interfaces according to A2A protocol
    supported_interfaces = [
        AgentInterface(
            url=agent_url,
            protocol_binding="HTTP+JSON",
            protocol_version="1.0",
        )
    ]

    agent_card = AgentCard(
        name="CountLettersAgent",
        description="Analyzes text to count letters and provide detailed reasoning about letter counts in questions.",
        version="1.0.0",
        # Backward compatibility with older A2A .NET client
        url=agent_url,
        protocol_version="1.0",
        # A2A v1.0 spec fields
        supported_interfaces=supported_interfaces,
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        capabilities=capabilities,
        skills=[count_letters_skill],
    )

    # Return with by_alias=False to use camelCase field names
    return JSONResponse(content=agent_card.model_dump(mode="json", by_alias=False))
