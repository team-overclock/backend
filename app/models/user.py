from sqlalchemy import Column, Integer, String
from ..database import Base

class User(Base):
    __tablename__ = "sign_up"

    seq = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(45), nullable=False)
    e_mail = Column(String(45), unique=True, index=True, nullable=False)
    passwd = Column(String(255), nullable=False) # 넉넉하게 255자로 설정 권장
    region = Column(String(45), nullable=True)