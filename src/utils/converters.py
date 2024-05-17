from src.users.models import User
from src.auth.schemas import UserInDB
from src.database.models import UserDB


def convert_IN_to_DB_model(user: User) -> UserDB:
    return UserDB(
        id=user.id,
        username=user.username,
        email=user.email,
        name=user.name,
        surname=user.surname,
        image=user.image,
        group_id=user.group_id.hex,
        role=user.role,
        phone=user.phone,
        hashed_password=user.hashed_password,
        is_blocked=user.is_blocked,
        created_at=user.created_at,
        modified_at=user.modified_at,
    )


def convert_AUTH_to_DB(user: UserInDB) -> UserDB:
    return UserDB(
        username=user.username,
        phone=user.phone,
        email=user.email,
        hashed_password=user.hashed_password,
    )
