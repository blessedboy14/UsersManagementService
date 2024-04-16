from sqlalchemy import URL


db_username = "blessedboy"
db_password = "ewkere123"
db_url = "localhost:5432"
db_schema = "management_service"

url = URL.create(
    drivername="postgresql+asyncpg",
    username=db_username,
    password=db_password,
    host=db_url,
    database=db_schema,
)


string_url = f"postgresql+asyncpg://{db_username}:{db_password}@{db_url}/{db_schema}"

