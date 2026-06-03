from .database import base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship

class Post(base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    content = Column(String(2000), nullable=False)
    published = Column(Boolean, nullable=False, server_default="1")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    user_id = user_id = Column(Integer, ForeignKey("users.id",ondelete="CASCADE"), nullable=False)
    owner = relationship("User")

class User(base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(254), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())


class Vote(base):
    __tablename__ = "votes"

    user_id = Column(Integer, ForeignKey("users.id",ondelete="CASCADE"), primary_key=True)
    post_id = Column(Integer, ForeignKey("posts.id",ondelete="CASCADE"), primary_key=True)
    
    