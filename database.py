from sqlmodel import create_engine, Session, SQLModel
from typing import Annotated
from fastapi import Depends
# Database connection

from dotenv import load_dotenv
import os

load_dotenv()


USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
DATABASE_NAME = os.getenv("DATABASE_NAME")



engine = create_engine(
    f"mysql+pymysql://{USERNAME}:{PASSWORD}@localhost:3306/{DATABASE_NAME}"
)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)



def get_session():
    with Session(engine) as session:
        yield session

dep = Annotated[Session, Depends(get_session)] 

# print(f"USERNAME: {USERNAME}")
# print(f"PASSWORD: {PASSWORD}")  
# print(f"DATABASE_NAME: {DATABASE_NAME}")