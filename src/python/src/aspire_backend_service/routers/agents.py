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


# A2A Protocol Models
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
async def count_letters_a2a(request_obj: Request) -> JSONResponse:
    """
    A2A JSON-RPC 2.0 endpoint for counting letters.
    Accepts: {"jsonrpc": "2.0", "method": "run", "params": "...", "id": 1}
    Returns: JSON-RPC 2.0 response
    """
    try:
        body = await request_obj.body()
        body_str = body.decode("utf-8")
        logger.info(f"A2A endpoint - Raw request body: {body_str}")

        body_json = json.loads(body_str)

        # Parse as JSON-RPC request
        jsonrpc_request = JsonRpcRequest(**body_json)
        logger.info(f"JSON-RPC method: {jsonrpc_request.method}, params: {jsonrpc_request.params}")

        # Extract the question from params
        # The A2A protocol can send params in various formats:
        # 1. As a string: "params": "question text"
        # 2. As a dict with question: "params": {"question": "..."}
        # 3. As an array: "params": ["question text"]
        # 4. As a dict with input: "params": {"input": "..."}
        if isinstance(jsonrpc_request.params, str):
            question = jsonrpc_request.params
        elif isinstance(jsonrpc_request.params, dict):
            # Try multiple keys that might contain the question
            question = (
                jsonrpc_request.params.get("question")
                or jsonrpc_request.params.get("input")
                or jsonrpc_request.params.get("text")
                or jsonrpc_request.params.get("prompt")
            )
            if not question:
                    logger.error(f"No recognized field in params: {jsonrpc_request.params}")
                error_response = JsonRpcErrorResponse(
                    error=JsonRpcError(
                        code=-32602,
                            message="Invalid params - expected A2A message structure with message.parts[].text",
                        data={"received": jsonrpc_request.params},
                    ),
                    id=jsonrpc_request.id,
                )
                return JSONResponse(content=error_response.model_dump(), status_code=400)
        elif isinstance(jsonrpc_request.params, str):
            # Legacy support: direct string params
            question = jsonrpc_request.params
        elif isinstance(jsonrpc_request.params, list) and len(jsonrpc_request.params) > 0:
            # Legacy support: array params
            question = (
                jsonrpc_request.params[0]
                if isinstance(jsonrpc_request.params[0], str)
                else str(jsonrpc_request.params[0])
            )
        else:
            logger.error(
                f"Unexpected params format: {jsonrpc_request.params} (type: {type(jsonrpc_request.params)})"
            )
            error_response = JsonRpcErrorResponse(
                error=JsonRpcError(
                    code=-32602,
                    message="Invalid params - expected A2A message structure",
                    data={
                        "received": jsonrpc_request.params,
                        "type": str(type(jsonrpc_request.params)),
                    },
                ),
                id=jsonrpc_request.id,
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

        # Generate UUIDs for A2A protocol
        import uuid

        task_id = str(uuid.uuid4())
        context_id = str(uuid.uuid4())
        message_id = str(uuid.uuid4())

        # According to A2A spec section 3.1.1, SendMessage can return either:
        # - A Task object (for async processing)
        # - A Message object (for simple synchronous interactions)
        #
        # Since we're doing synchronous processing, return a Message directly
        # instead of a Task with Completed status
        a2a_message = {
            "kind": "message",
            "messageId": message_id,
            "role": "Agent",  # .NET expects PascalCase role
            "parts": [{"kind": "text", "text": answer_text}],
            }

        # Return JSON-RPC response with A2A Message object
        jsonrpc_response = JsonRpcResponse(result=a2a_message, id=jsonrpc_request.id)
        response_data = jsonrpc_response.model_dump()
        logger.info(
            f"Returning A2A-compliant JSON-RPC response with Message object: {json.dumps(response_data)}"
        )
        return JSONResponse(content=response_data)

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}")
        error_response = JsonRpcErrorResponse(
            error=JsonRpcError(code=-32700, message="Parse error", data=str(e)), id=None
        )
        return JSONResponse(content=error_response.model_dump(), status_code=400)
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        error_response = JsonRpcErrorResponse(
            error=JsonRpcError(code=-32600, message="Invalid Request", data=e.errors()), id=None
        )
        return JSONResponse(content=error_response.model_dump(), status_code=400)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        error_response = JsonRpcErrorResponse(
            error=JsonRpcError(code=-32603, message="Internal error", data=str(e)), id=None
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
