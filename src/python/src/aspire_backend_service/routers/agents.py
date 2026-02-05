from fastapi import APIRouter

from ..agents.hello import hello
from ..agents.calculator import calculator

from .request_models import CountLettersRequest

router = APIRouter(
    prefix="/agents",
    tags=["agents"],
    responses={ 404: { "description": "Not Found" }},
)

@router.get("/hello-world")
async def hello_world():
    """
    This is a test method to validate if the application
    working and we get a response using the pattern of
    creating an object and invoking a method.
    """
    subject = hello()
    response_message = await subject.run()
    return {
        "message": response_message
    }

@router.post("/count-letters")
async def count_letters(request: CountLettersRequest):
    subject = calculator()
    answer = await subject.run(request.question)
    return {
        "count": answer
    }
