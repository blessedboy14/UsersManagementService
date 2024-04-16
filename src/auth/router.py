from fastapi import APIRouter


auth = APIRouter()


@auth.post("/login")
async def login():
    pass


@auth.post("/signup")
async def signup():
    pass


@auth.post("/reset-password")
async def signup():
    pass


@auth.post("/refresh-token")
async def signup():
    pass

