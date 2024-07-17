from fastapi import APIRouter, status

router = APIRouter()


@router.get(
    '/health_check', status_code=status.HTTP_200_OK, summary='Check Server Work'
)
async def health_check():
    return {'status': 'running'}
