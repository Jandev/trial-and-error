from fastapi import APIRouter
from pydantic import BaseModel

from ..agents.calculator import calculator
from ..agents.hello import hello
from .request_models import CountLettersRequest

router = APIRouter(
    prefix="/agents",
    tags=["agents"],
    responses={404: {"description": "Not Found"}},
)


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
