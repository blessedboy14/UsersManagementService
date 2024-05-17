from fastapi import APIRouter
from starlette import status

router = APIRouter()


@router.get(
    '/health_check', status_code=status.HTTP_200_OK, summary='Check Server Work'
)
async def health_check():
    return {'status': 'running'}
