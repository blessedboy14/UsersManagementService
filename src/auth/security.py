from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer

from src.auth.models import UserIn, UserInDB


SECRET_KEY = "qemnk5lu6z1bdbedgin85zhi47cgvu6lqokab9lilx49odbbpvdflbrlhq15nbk7"
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 120


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def hash_model(user: UserIn) -> UserInDB:
    user.password = get_password_hash(user.password)
    return UserInDB(
        username=user.username,
        phone=user.phone,
        email=user.email,
        hashed_password=user.password
    )


