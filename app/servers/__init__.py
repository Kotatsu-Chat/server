from sqlmodel import Session, select
from app.database import Server, engine, ParameterID, Invite, DBUser
from app.snowflakes import snowfactory


def create_new_server(server_name: str, owner_id: int):
    with Session(engine) as session:
        server = Server(server_name=server_name, server_owner_id=owner_id, users=f"[{owner_id}]",
                        snowflake=snowfactory.generate(ParameterID.SERVER.value))
        user = session.get(DBUser,owner_id)
        user.servers.append(server)
        server.users.append(user)
        session.add(server)
        session.add(user)
        session.commit()
        return server

def generate_invite(server_snowflake: int, user_snowflake: int):
    with Session(engine) as session:
        server = session.get(Server, server_snowflake)
        if server:
            user = session.get(DBUser,user_snowflake)
            if user:
                if user in server.users:
                    invite = Invite(snowflake = snowfactory.generate(ParameterID.INVITE.value), server_snowflake = server.snowflake)
                    session.add(invite)
                    session.commit
                    return invite

def user_join_server(invite_snowflake: int, user_snowflake: int):
    with Session(engine) as session:
        invite = session.get(Invite,invite_snowflake)
        server = session.get(Server,invite.server_snowflake)
        user = session.get(DBUser,user_snowflake)
        server.users.append(user)
        user.servers.append(server)
        session.add(server)
        session.add(user)
        session.commit
        return 200