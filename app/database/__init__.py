from typing import Optional, Annotated, List

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlmodel import Field, SQLModel, create_engine, Session, select, Relationship
from fastapi import status

from app.models import User
from app.snowflakes import snowfactory, ParameterID


class Message(SQLModel, table=True):
    snowflake: int = Field(unique=True, primary_key=True, nullable=False)
    message: str = Field(nullable=False)
    channel: int = Field(nullable=False)
    userid: int = Field(nullable=False)
    editflag: int = Field(nullable=False, default=0)

class Invite(SQLModel, table=True):
    snowflake: int = Field(unique=True, primary_key=True, nullable=False)
    server_snowflake: int


class MessageReply(SQLModel, table=False):
    message: Message
    user: User


class Role(SQLModel, table=True):
    snowflake: int = Field(unique=True, primary_key=True, nullable=False)
    permissions_bitfield: int = Field(nullable=False)
    name: str = Field(nullable=False)
    server_id: int = Field(nullable=False)


class Server(SQLModel, table=True):
    snowflake: int = Field(unique=True, primary_key=True, nullable=False)
    channels: Optional[str] = "[]"
    users: List["DBUser"] = Relationship(back_populates="users") #Field(nullable=False)
    roles: Optional[str] = "[]"
    server_name: str = Field(nullable=False)
    nicknames: Optional[str] = "{}"
    server_owner_id: int = Field(nullable=False)


class DBUser(User, table=True):
    __tablename__ = "user"

    snowflake: int = Field(unique=True, primary_key=True, nullable=False)
    username: str = Field(nullable=False)
    password_hashed: str = Field(nullable=False)
    servers: List["Server"] = Relationship(back_populates="servers") #str = Field(nullable=False)


sqlite_file_name = "main.db"
sqlite_url = f"sqlite:///userdata/{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=True, pool_pre_ping=True)

SQLModel.metadata.create_all(engine)


def create_message(message: str, channelid: int, userid: int) -> MessageReply:
    """

    returns a Message object that's been written to the server.
    """
    snowflakeid = snowfactory.generate(ParameterID.MESSAGE.value)
    message = Message(snowflake=snowflakeid, channel=channelid,
                      userid=userid, message=message, editflag=0)

    with Session(engine) as session:
        session.add(message)
        session.commit()

    with Session(engine) as session:
        statement = select(Message).where(Message.snowflake == snowflakeid)
        results = session.exec(statement)
        replymessage = results.first()
        userstatement = select(DBUser).where(DBUser.snowflake == replymessage.model_dump()["userid"])
        userresults = session.exec(userstatement)
        user = userresults.one()
        userdump = user.model_dump()
        userdump.pop("password_hashed")
        user = User(snowflake=userdump["snowflake"], username=userdump["username"], servers=userdump["servers"])
        return MessageReply(message=replymessage, user=user)



def get_message_from_id(channel_id: int, message_id: int) -> MessageReply:
    with Session(engine) as session:
        statement = select(Message).where(Message.snowflake == message_id)
        results = session.exec(statement)
        message = results.first()
        userstatement = select(DBUser).where(DBUser.snowflake == message.model_dump()["userid"])
        userresults = session.exec(userstatement)
        user = userresults.one()
        userdump = user.model_dump()
        userdump.pop("password_hashed")
        user = User(snowflake=userdump["snowflake"], username=userdump["username"], servers=userdump["servers"])
        return MessageReply(message=message, user=user)


def get_message_near_id(channel_id: int, message_id: int, count: int = 25, type: int = -1) -> list[MessageReply]:
    """
    returns a list of Message objects
    :param channel_id: channel to get messages in
    :param message_id: base message
    :param count: amount of messages to get
    :param type: -1 = before this message, 1 = after the message. 0 is null for now.
    :return: a list of Messages
    """
    count = max(min(count, 50), 1)
    if type == 1:
        with Session(engine) as session:
            statement = select(Message).where(Message.snowflake > message_id).where(Message.channel == channel_id).order_by(Message.snowflake.asc()).limit(count)
            results = session.exec(statement)
            resultlist = []
            for res in results:
                userstatement = select(DBUser).where(DBUser.snowflake == res.model_dump()["userid"])
                userresults = session.exec(userstatement)
                user = userresults.one()
                userdump = user.model_dump()
                userdump.pop("password_hashed")
                user = User(snowflake=userdump["snowflake"], username=userdump["username"], servers=userdump["servers"])
                resultlist.append(MessageReply(message=res, user=user))
    else:
        with Session(engine) as session:
            statement = select(Message).where(Message.snowflake < message_id).where(Message.channel == channel_id).order_by(Message.snowflake.desc()).limit(count).order_by(Message.snowflake.asc())
            results = session.exec(statement)
            resultlist = []
            for res in results:
                userstatement = select(DBUser).where(DBUser.snowflake == res.model_dump()["userid"])
                userresults = session.exec(userstatement)
                user = userresults.one()
                userdump = user.model_dump()
                userdump.pop("password_hashed")
                user = User(snowflake=userdump["snowflake"], username=userdump["username"], servers=userdump["servers"])
                resultlist.append(MessageReply(message=res, user=user))
    return resultlist