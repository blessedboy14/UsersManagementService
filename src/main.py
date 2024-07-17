import contextlib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.drivers.rest.exception_handlers import exception_container
from src.drivers.rest.routers import auth
from src.drivers.rest.routers import common
from src.drivers.rest.routers import users
from src.database.database import session_manager


@contextlib.asynccontextmanager
async def lifespan(_: FastAPI):
    yield

    if session_manager.get_engine() is not None:
        await session_manager.close()


origins = [
    'http://localhost:5173',
    'http://localhost:5173/',
    'http://localhost:3000',
    'http://localhost:3000/',
]


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
app.include_router(auth.router, prefix='/auth', tags=['auth'])
app.include_router(common.router, prefix='', tags=['common'])
app.include_router(users.router, prefix='/users', tags=['users'])


exception_container(app)
