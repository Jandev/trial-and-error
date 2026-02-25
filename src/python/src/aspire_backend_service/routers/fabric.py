from fastapi import APIRouter, HTTPException

from ..infrastructure.fabric_sql import query_to_dataframe

router = APIRouter()


@router.get("/api/query")
async def query_fabric():
    sql = """
    SELECT *
    FROM [database].[dbo].[table]
    """

    try:
        df = query_to_dataframe(sql)
        return df.to_dict(orient="records")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
