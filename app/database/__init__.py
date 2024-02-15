from typing import Optional, Annotated

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlmodel import Field, SQLModel, create_engine, Session, select
from fastapi import status

from app.models import User



class Message(SQLModel, table=True):
    snowflake: int = Field(unique=True, primary_key=True, nullable=False)
    message: str = Field(nullable=False)
    channel: int = Field(nullable=False)
    userid: int = Field(nullable=False)
    editflag: int = Field(nullable=False, default=0)


class Role(SQLModel, table=True):
    snowflake: int = Field(unique=True, primary_key=True, nullable=False)
    permissions_bitfield: int = Field(nullable=False)
    name: str = Field(nullable=False)
    server_id: int = Field(nullable=False)


class Server(SQLModel, table=True):
    snowflake: int = Field(unique=True, primary_key=True, nullable=False)
    channels: str = Field(nullable=False)
    users: str = Field(nullable=False)
    roles: str = Field(nullable=False)
    server_name: str = Field(nullable=False)
    nicknames: str = Field(nullable=False)
    server_owner_id: int = Field(nullable=False)


class DBUser(User, table=True):
    __tablename__ = "user"

    snowflake: int = Field(unique=True, primary_key=True, nullable=False)
    username: str = Field(nullable=False)
    password_hashed: str = Field(nullable=False)
    servers: str = Field(nullable=False)

sqlite_file_name = "main.db"
sqlite_url = f"sqlite:///userdata/{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=True, pool_pre_ping=True)

SQLModel.metadata.create_all(engine)


