from sqlmodel import Session
from app.database import Server
from flakemaker import SnowflakeGenerator



def create_new_server(server_name: str, owner_id: int):
    server = Server(server_name = server_name, server_owner_id = owner_id,
                  snowflake=SnowflakeGenerator().generate(69))
    with Session(engine) as session:
        session.add(server)
        session.commit()
        return server
