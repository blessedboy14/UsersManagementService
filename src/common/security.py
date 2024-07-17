from jose import jwt, JWTError
from fastapi import HTTPException
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from datetime import timedelta, datetime

from src.common.config import logger
from src.config.settings import settings
from src.drivers.rest.routers.schema import UserIn, UserInDB

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_EXP = timedelta(minutes=settings.access_exp)
REFRESH_EXP = timedelta(days=settings.refresh_exp)

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
