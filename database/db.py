# import os
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from database.models import Base
# from dotenv import load_dotenv

# load_dotenv()

# # Support both .env (local) and Streamlit Cloud secrets
# try:
#     import streamlit as st
#     DATABASE_URL = st.secrets.get("DATABASE_URL") or os.getenv("DATABASE_URL")
# except Exception:
#     DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:password@localhost:3306/mini_crm")

# engine = create_engine(DATABASE_URL, pool_pre_ping=True)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# def init_db():
#     Base.metadata.create_all(bind=engine)


# def get_session():
#     return SessionLocal()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base

DATABASE_URL = "mysql+pymysql://root:Hello1234@localhost:3306/mini_crm"

print("DATABASE_URL =", DATABASE_URL)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_session():
    return SessionLocal()