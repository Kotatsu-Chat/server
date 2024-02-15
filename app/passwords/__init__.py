import datetime
from typing import Annotated

from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlmodel import select, Session
from starlette import status

from app.database import DBUser, engine, AppSecrets
from app.models import User
from app.secrets import secrets

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Token(BaseModel):
    access_token: str
    token_type: str


def get_secrets():
    return secrets


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_user(username: str):
    with Session(engine) as session:
        statement = select(DBUser).where(DBUser.username == username)
        results = session.exec(statement)
        user = results.first()
        user = user.model_dump() if user is not None else None
        return user


def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user['password_hashed']):
        return False
    return user


def fake_decode_token(token):
    # This doesn't provide any security at all
    # Check the next version
    user = get_user(token)
    return user


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    user = fake_decode_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_active_user(
        current_user: Annotated[User, Depends(get_current_user)]
):
    return current_user


def create_access_token(data: dict, expires_delta: datetime.timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.now(datetime.timezone.utc) + expires_delta
    else:
        expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, get_secrets()['bcrypt_secret_key'], algorithm=ALGORITHM)
    return encoded_jwt
