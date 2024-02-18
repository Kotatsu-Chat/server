from sqlmodel import Session
from app.database import Server, engine, ParameterID
from app.snowflakes import snowfactory


def create_new_server(server_name: str, owner_id: int):
    server = Server(server_name=server_name, server_owner_id=owner_id, users=f"[{owner_id}]",
                    snowflake=snowfactory.generate(ParameterID.SERVER.value))
    with Session(engine) as session:
        session.add(server)
        session.commit()
        return server
