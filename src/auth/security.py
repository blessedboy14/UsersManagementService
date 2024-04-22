from jose import jwt, JWTError
from fastapi import HTTPException
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, HTTPBearer
from datetime import timedelta, datetime

from src.auth.models import UserIn, UserInDB


SECRET_KEY = '68d5b14da586a1cf8609325abc54a3da88c410e828307e3eded230a58a2a3d8e'
ALGORITHM = 'HS256'
ACCESS_EXP = timedelta(minutes=60)
REFRESH_EXP = timedelta(days=31)


pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/login')
bearer = HTTPBearer()


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
        hashed_password=user.password,
    )


def create_access_jwt(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + ACCESS_EXP
    to_encode.update({'exp': expire})
    to_encode.update({'mode': 'access_token'})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, ALGORITHM)
    return encoded_jwt


def create_refresh_jwt(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + REFRESH_EXP
    to_encode.update({'exp': expire})
    to_encode.update({'mode': 'refresh_token'})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, ALGORITHM)
    return encoded_jwt


async def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, ALGORITHM)
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail='Invalid token')
