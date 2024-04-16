from fastapi import FastAPI
from starlette.responses import RedirectResponse
from .auth.router import auth
from .common.router import common
from .users.router import users_router

app = FastAPI()

app.include_router(auth, prefix="/auth", tags=["auth"])
app.include_router(common, prefix="", tags=["common"])
app.include_router(users_router, prefix="/users", tags=["users"])


@app.get("/")
def main_function():
    return RedirectResponse(url="/docs/")
