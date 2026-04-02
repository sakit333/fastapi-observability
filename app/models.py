from sqlalchemy import Column, Integer, String, Float
import uuid
from sqlalchemy.dialects.postgresql import UUID
from passlib.context import CryptContext
from db import Base

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone_number = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)

    def verify_password(self, password: str) -> bool:
        return pwd_context.verify(password, self.password)

    @staticmethod
    def hash_password(password: str) -> str:
        password = password.encode("utf-8")[:72]  # ✅ truncate safely
        return pwd_context.hash(password)

# 1. Define a quick Product model if you haven't already
class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    price = Column(Float)