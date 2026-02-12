from pydantic import BaseModel


class CountLettersRequest(BaseModel):
    question: str
