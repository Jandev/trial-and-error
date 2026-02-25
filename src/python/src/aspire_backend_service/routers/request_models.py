from pydantic import BaseModel


class CountLettersRequest(BaseModel):
    question: str


class LargeDataAnalysisRequest(BaseModel):
    query: str
