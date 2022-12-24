from enum import unique
from operator import index
from sqlalchemy import  Column, Integer, String, ForeignKey,true
from database import Base
from sqlalchemy.orm import relationship


class user_register(Base):
   
    __tablename__ = "user_register_table"
    id           = Column(Integer, primary_key=True, autoincrement=True, index=True, nullable=False)
    name         = Column(String(255), index=True, nullable=False)
    email        = Column(String(100), index=True, nullable=False,unique=True)
    mobile_no    = Column(String(100), index=True, nullable=False,unique=True)
    sex          =Column(String(255),index=true,nullable=False)
    dob          =Column(String(255),index=true,nullable=False)
    password     =Column(String(255),index=True, nullable=False, unique=True)
