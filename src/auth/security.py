from jose import jwt, JWTError
from fastapi import HTTPException
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from datetime import timedelta, datetime

from src.config.settings import logger
from src.auth.models import UserIn, UserInDB

SECRET_KEY = 'H45SHvuxLkgEKzKt1HyMXSyt1Vtl2YL4b5zUf3q46Ou+KrZYq+yD7x2bTM+N3W0lqxqGRsdky4xG+hIx+fb67A=='
ALGORITHM = 'HS256'
ACCESS_EXP = timedelta(minutes=60)
REFRESH_EXP = timedelta(days=31)

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/login')


def verify_password(plain_password, hashed_password) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password) -> str:
    return pwd_context.hash(password)


def hash_model(user: UserIn) -> UserInDB:
    user.password = get_password_hash(user.password)
    return UserInDB(
        username=user.username,
        phone=user.phone,
        email=user.email,
        hashed_password=user.password,
    )


def create_access_jwt(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + ACCESS_EXP
    to_encode.update({'exp': expire})
    to_encode.update({'mode': 'access_token'})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, ALGORITHM)
    return encoded_jwt


def create_refresh_jwt(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + REFRESH_EXP
    to_encode.update({'exp': expire})
    to_encode.update({'cur_date': datetime.utcnow().isoformat()})
    to_encode.update({'mode': 'refresh_token'})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, ALGORITHM)
    return encoded_jwt


def create_link_token(data: dict) -> str:
    to_encode = data.copy()
    encoded = jwt.encode(to_encode, SECRET_KEY, ALGORITHM)
    return encoded


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, ALGORITHM)
        return payload
    except JWTError as e:
        logger.error(f'Token expired or other error: {e}')
        raise HTTPException(status_code=401, detail='Token invalid')
