from fastapi import FastAPI
from .auth.router import auth
from .common.router import common


app = FastAPI()


app.include_router(auth, prefix="/auth", tags=["auth"])
app.include_router(common, prefix="", tags=["common"])

