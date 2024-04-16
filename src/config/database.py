from sqlalchemy import create_engine, URL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


db_username = "blessedboy"
db_password = "ewkere123"
db_url = "localhost:5432"
db_schema = "postgres"

url = URL.create(
    drivername="postgresql",
    username=db_username,
    password=db_password,
    host=db_url,
    database=db_schema,
)


engine = create_engine(url, echo=False)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base = declarative_base()

