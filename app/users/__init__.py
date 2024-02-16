import datetime
from typing import Annotated

from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlmodel import select, Session
from starlette import status

from app.database import DBUser, engine
from app.models import User
from app.secrets import secrets
from app.snowflakes import SnowflakeFactory, ParameterID

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


def create_new_user(username: str, password: str):
    user = DBUser(username=username, password_hashed=hash_password(password),
                  snowflake=SnowflakeFactory.get_snowflake(ParameterID.USER.value), servers=str([]))
    with Session(engine) as session:
        session.add(user)
        session.commit()
        return user


def get_user(username: str):
    with Session(engine) as session:
        statement = select(DBUser).where(DBUser.username == username)
        results = session.exec(statement)
        user = results.first()
        user = user.model_dump() if user is not None else None
        return user


def get_user_from_id(user_id: int):
    with Session(engine) as session:
        statement = select(DBUser).where(DBUser.snowflake == user_id)
        results = session.exec(statement)
        user = results.first()
        user = user.model_dump() if user is not None else None
        user.pop("password_hashed")
        return user


def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user['password_hashed']):
        return False
    return user


class TokenData(BaseModel):
    username: str | None = None


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, get_secrets()['bcrypt_secret_key'], algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    user.pop("password_hashed")
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
