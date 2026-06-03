from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from . import models 
from .database import engine
from . import schemas
from .routers import posts, users, auth, vote
from .config import settings



# models.base.metadata.create_all(bind=engine)
# alembic can handle database migrations, so we don't need to create tables manually here.


app = FastAPI()
origin = ['https://www.google.com', 'https://www.youtube.com'] # * for everyone can access 
# best practice to define scope of domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (you can specify specific origins if needed)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

@app.get('/',status_code=status.HTTP_200_OK, response_model=schemas.MessageResponse)
def root():
  return {'message': 'Welcome to my API!'}

app.include_router(posts.router)
app.include_router(users.router)
app.include_router(auth.router)
app.include_router(vote.router)