from fastapi import HTTPException, status, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from .. import models
from ..database import get_db
from .. import schemas
from .. import utils

from fastapi import APIRouter

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.post('/', status_code=status.HTTP_201_CREATED, response_model=schemas.MessageResponse)
def create_user(user: schemas.User, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email '{user.email}' already exists"
        )
    hashed_password = utils.hash_password(user.password)
    user.password = hashed_password
    new_user = models.User(**user.model_dump())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully"}


@router.get('/{id}', status_code=status.HTTP_200_OK, response_model=schemas.UserResponse)
def get_user(id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id {id} not found")
    return user
