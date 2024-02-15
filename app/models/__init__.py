from pydantic import BaseModel
from sqlmodel import SQLModel, Field


class ErrorDetail(BaseModel):
    detail: str


class ClientMessageSend(BaseModel):
    message: str


class User(SQLModel, table=False):
    snowflake: int = Field(unique=True, primary_key=True, nullable=False)
    username: str = Field(nullable=False)
    servers: str = Field(nullable=False)
