import contextlib

import aioredis
import uvicorn
from fastapi import FastAPI
from starlette.responses import RedirectResponse

from src.auth import auth
from src.common.router import common
from src.users import users
from src.database.database import session_manager


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):

    yield

    if session_manager.get_engine() is not None:
        await session_manager.close()


app = FastAPI(lifespan=lifespan)


app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(common, prefix="", tags=["common"])
app.include_router(users.router, prefix="/users", tags=["users"])


@app.get("/")
def start():
    return RedirectResponse(url="/docs/")
