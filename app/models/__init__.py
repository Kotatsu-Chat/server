from typing import Union

from pydantic import BaseModel
from sqlmodel import SQLModel, Field
from starlette.websockets import WebSocket


class ErrorDetail(BaseModel):
    detail: str


class ClientMessageSend(BaseModel):
    message: str


class User(SQLModel, table=False):
    snowflake: int = Field(unique=True, primary_key=True, nullable=False)
    username: str = Field(nullable=False)
    servers: str = Field(nullable=False)


class ConnectionManager:
    def __init__(self):
        # Store active connections as a list of lists, each containing a WebSocket and a channel_id
        self.active_connections: list[list[WebSocket, int]] = []

    async def connect(self, websocket: WebSocket, channel_id: int) -> None:
        # Accept the WebSocket connection and add it along with channel_id to active_connections
        await websocket.accept()
        self.active_connections.append([websocket, channel_id])

    def disconnect(self, websocket: WebSocket):
        # Find and remove the connection by matching the WebSocket
        self.active_connections = [conn for conn in self.active_connections if conn[0] != websocket]

    @staticmethod
    async def send_personal_message(message: str, websocket: WebSocket):
        # Send a message to a single WebSocket
        await websocket.send_text(message)

    async def broadcast(self, message: str, channel_id: int):
        # Broadcast a message to all WebSockets in the specified channel
        for connection in self.active_connections:
            if connection[1] == channel_id:  # Check if the connection is in the specified channel
                await connection[0].send_text(message)  # connection[0] is the WebSocket

