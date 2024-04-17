from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

common = APIRouter()


@common.get("/health_check")
async def health_check():
    return {"status": "ready"}