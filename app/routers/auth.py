from fastapi import HTTPException, status, Depends, APIRouter
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from .. import models
from ..database import get_db
from .. import schemas
from .. import utils  
from . import oauth2


router = APIRouter(
    prefix="/login",
    tags=["Authentication"]
)

@router.post('', status_code=status.HTTP_200_OK, response_model=schemas.Token)
def login(user: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.username).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid email or password")
    if not utils.verify_password(user.password, db_user.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid email or password")
    access_token = oauth2.create_access_token(data={"sub": db_user.email})
    return schemas.Token(message="Login successful", access_token=access_token, token_type="bearer")