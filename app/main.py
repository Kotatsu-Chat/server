from datetime import timedelta

from fastapi import FastAPI, Depends, status, HTTPException, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.exc import NoResultFound
from starlette.responses import Response
from starlette.websockets import WebSocket, WebSocketDisconnect

from app.database import User, create_message, Message, get_message_from_id, get_message_near_id, MessageReply
from app.users import Token, authenticate_user, ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token
from app.users import get_current_active_user, pwd_context, get_user, get_current_user, get_user_from_id, \
    create_new_user
from app.snowflakes import snowfactory
from app.models import ClientMessageSend, ErrorDetail, ConnectionManager

from typing import Annotated, List

app = FastAPI(title="Rollplayer Chat 3 API", version="0.0.1", root_path="/api")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@app.get("/test")
async def get_test():
    print(pwd_context.hash("123"))
    return {"message": ""}


@app.get("/users/me")
async def read_users_me(current_user: Annotated[User, Depends(get_current_active_user)]):
    return current_user


@app.get("/users/new", name="New User",
         description="Create a new user. Username limited to 64 chars, password limited to 72 chars")
async def new_user(username: Annotated[str | None, Query(max_length=64)],
                   password: Annotated[str | None, Query(max_length=72)], ):
    return create_new_user(username, password)


@app.get("/users/info/{user_id}")
async def read_user_from_id(user_id: int):
    return get_user_from_id(user_id)


manager = ConnectionManager()


@app.post("/channel/{channel_id}/sendmessage",
          status_code=status.HTTP_201_CREATED,
          responses={status.HTTP_400_BAD_REQUEST:
                         {"model": ErrorDetail,
                          "description": "The message was too long."}
                     })
async def send_message(channel_id: int, message: ClientMessageSend,
                       current_user: Annotated[User, Depends(get_current_active_user)]) -> MessageReply:
    if len(message.message) >= 4096:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message too long")
    created_message = create_message(message.message, channel_id, current_user["snowflake"])
    # Broadcast the message to all clients in the channel
    await manager.broadcast(str(created_message.model_dump_json()), channel_id)
    return created_message


@app.post("/channel/{channel_id}/getmessage/{message_id}")
async def get_message(channel_id: int, message_id: int,
                      current_user: Annotated[User, Depends(get_current_active_user)]) -> MessageReply:
    return get_message_from_id(channel_id, message_id)


@app.post("/channel/{channel_id}/getmessages/{message_id}",
          description="Gets messages before or after the message ID. `type` is the direction. -1 is before, 1 is after. Defaults to -1.",
          responses={status.HTTP_204_NO_CONTENT: {"description": "No messages found"}})
async def get_messages(channel_id: int, message_id: int,
                      count: Annotated[str | None, Query(max_length=5)],
                      type: Annotated[str | None, Query(max_length=5)],
                      current_user: Annotated[User, Depends(get_current_active_user)]):
    try:
        return get_message_near_id(channel_id, message_id, int(count), int(type))
    except NoResultFound as e:
        return Response(status_code=204)




@app.get("/channel/{channel_id}/listen", name="WebSocket Channel Listening Endpoint", description="""
This endpoint is actually a websocket interface - GETting from it will do nothing and return a 200.
You can attach to it using websockets, then just listening for a message [in MessageReply format].
Later, this will ask for an authentication token, but it doesn't currently.""")
async def listen():
    return ""


@app.websocket("/channel/{channel_id}/listen")
async def websocket_endpoint(channel_id: int, websocket: WebSocket):
    await manager.connect(websocket, channel_id)
    try:
        pass
        # token = await websocket.receive_text()
        # user = get_current_user(token)
        # TODO: validate user is in the server that the channel is in
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    try:
        while True:
            # Wait for any message to manage the connection, but don't use the data
            await websocket.receive_text()
            # No broadcasting here, as this endpoint is for listening
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/snowflake/info/{snowflake}",
         description="Parses a snowflake and gets information about it [the type of snowflake]")
async def snowflake_info(snowflake: int):
    return {"type": snowfactory.parse(str(snowflake))[1]}


@app.post("/token")
async def login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

@app.post("/severs/new",name='New User',description='Create a new server. Server name is limited to 32 chars.')
async def new_server(server_name: Annotated[str | None, Query(max_length=32)], user: Annotated[User, Depends(get_current_active_user)]) -> int:
    return create_new_server(server_name,user["snowflake"])["snowflake"]