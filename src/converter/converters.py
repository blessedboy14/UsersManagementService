from src.users.models import User
from src.database.models import UserDB


def convert_IN_to_DB_model(user: User) -> UserDB:
    return UserDB(
        username=user.username,
        email=user.email,
        name=user.name,
        surname=user.surname,
        image=user.image,
        group=user.group,
        role=user.role,
        phone=user.phone,
        hashed_password=user.hashed_password,
        is_blocked=user.is_blocked,
    )
