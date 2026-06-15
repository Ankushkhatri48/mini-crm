# import os
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from database.models import Base
# from dotenv import load_dotenv

# load_dotenv()

# try:
#     import streamlit as st
#     DATABASE_URL = st.secrets["DATABASE_URL"]
# except Exception:
#     DATABASE_URL = os.getenv(
#         "DATABASE_URL",
#         "mysql+pymysql://root:password@localhost:3306/mini_crm"
#     )

# print("Database connection loaded")

# engine = create_engine(
#     DATABASE_URL,
#     pool_pre_ping=True
# )

# SessionLocal = sessionmaker(
#     autocommit=False,
#     autoflush=False,
#     bind=engine
# )

# def init_db():
#     Base.metadata.create_all(bind=engine)

# def get_session():
#     return SessionLocal()

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base
from dotenv import load_dotenv

load_dotenv()

try:
    import streamlit as st
    DATABASE_URL = st.secrets["DATABASE_URL"]
except Exception:
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:password@localhost:3306/mini_crm"
    )

print("Database configuration loaded")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_session():
    return SessionLocal()