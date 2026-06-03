from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, Any

class User(BaseModel):
    email: EmailStr
    password: str

    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True

class Post(BaseModel):
  title: str
  content: str
  published: bool = True
  


class PostResponse(Post):
  id: int
  created_at: datetime
  user_id: int
  owner: UserResponse
  


  class Config:
    from_attributes = True


class MessageResponse(BaseModel):
  message: str


class CreatePostResponse(BaseModel):
  message: str
  post: PostResponse

  class Config:
    from_attributes = True


class SinglePostResponse(BaseModel):
  success: bool
  response: Optional[PostResponse | str] = None

  class Config:
    from_attributes = True

class PostOut(BaseModel):
    Post : PostResponse
    votes: int

    class Config:
        from_attributes = True


class ActionResponse(BaseModel):
  success: bool
  message: str

  class Config:
    from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

    class Config:
        from_attributes = True

class Token(MessageResponse):
    access_token: str
    token_type: str

    class Config:
        from_attributes = True


class TokenData(BaseModel):
    email: Optional[EmailStr] = None

    class Config:
        from_attributes = True


class Vote(BaseModel):
    post_id: int
    dir: int

    class Config:
        from_attributes = True



