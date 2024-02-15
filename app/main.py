from datetime import timedelta

from fastapi import FastAPI, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from app.database import User
from app.passwords import Token, authenticate_user, ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, \
    get_current_active_user, pwd_context
from app.snowflakes import SnowflakeFactory
from app.models import ClientMessageSend, ErrorDetail

from typing import Annotated
app = FastAPI(title="Rollplayer Chat 3 API", version="0.0.1")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.get("/test")
async def get_test():
    print(pwd_context.hash("example"))
    return {"message": ""}
@app.get("/users/me")
async def read_users_me(current_user: Annotated[User, Depends(get_current_active_user)]):
    return current_user

@app.post("/message/send/{server_id}/{channel_id}",
          status_code=status.HTTP_201_CREATED,
          responses={status.HTTP_400_BAD_REQUEST:
                         {"model": ErrorDetail,
                          "description": "The message was too long."}
                     })
async def send_message(server_id: int, channel_id: int, message: ClientMessageSend, token: Annotated[str, Depends(oauth2_scheme)]):
    print(message, server_id, channel_id)
    if len(message.message) >= 4096:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message too long")
    return message

    return {"message": messagereturn.message, "server_id": server_id, "channel_id": channel_id, "snowflake": 0}



@app.get("/snowflake/info/{snowflake}",
         description="Parses a snowflake and gets information about it [the type of snowflake]")
async def snowflake_info(snowflake: int):
    return {"type": SnowflakeFactory.parse_snowflake(str(snowflake))[1]}



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
