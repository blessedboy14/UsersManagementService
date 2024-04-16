from fastapi import APIRouter


common = APIRouter()


@common.get("/health_check")
async def health_check():
    return {"status": "ready"}
