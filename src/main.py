import contextlib
from fastapi import FastAPI

from src.drivers.rest.exception_handlers import exception_container

# from src.auth import auth
from src.drivers.rest.routers import auth
from src.drivers.rest.routers import common

# from src.users import users
from src.drivers.rest.routers import users
from src.database.database import session_manager


@contextlib.asynccontextmanager
async def lifespan(_: FastAPI):
    yield

    if session_manager.get_engine() is not None:
        await session_manager.close()


app = FastAPI(lifespan=lifespan)
app.include_router(auth.router, prefix='/auth', tags=['auth'])
app.include_router(common.router, prefix='', tags=['common'])
app.include_router(users.router, prefix='/users', tags=['users'])


exception_container(app)
