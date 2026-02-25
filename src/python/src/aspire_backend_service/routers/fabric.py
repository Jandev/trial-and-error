from fastapi import APIRouter, HTTPException

from ..infrastructure.data_access import get_customer_information

router = APIRouter()


@router.get("/api/query")
async def query_fabric():
    try:
        return get_customer_information()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
