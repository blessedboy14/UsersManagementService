from fastapi import APIRouter

common = APIRouter()


@common.get('/health_check', summary='Check Server Work')
async def health_check():
    return {'status': 'running'}
