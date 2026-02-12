from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..agents.calculator import calculator
from ..agents.hello import hello
from .request_models import CountLettersRequest

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
    defaultInputModes: list[str] = Field(alias="default_input_modes")
    defaultOutputModes: list[str] = Field(alias="default_output_modes")
    capabilities: AgentCapabilities
    skills: list[AgentSkill]

    class Config:
        populate_by_name = True


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
    subject = calculator()
    results = await subject.run(request.question)

    if results is None:
        return count_letters_response(answer="", finalNumber=0, reasoning="", chainOfThought="")

    responseValue = count_letters_response(
        answer=results.answer,
        chainOfThought=results.chain_of_thought,
        reasoning=results.reasoning,
        finalNumber=results.final_number,
    )

    return responseValue


@router.get("/count-letters/.well-known/agent-card.json")
async def get_count_letters_agent_card() -> AgentCard:
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

    return AgentCard(
        name="CountLettersAgent",
        description="Analyzes text to count letters and provide detailed reasoning about letter counts in questions.",
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=capabilities,
        skills=[count_letters_skill],
    )
