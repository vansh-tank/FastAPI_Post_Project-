from typing import Optional
from fastapi import HTTPException, status, Depends, APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.orm import Session
from .. import models
from ..database import get_db, get_raw_db
from .. import schemas
from .. import utils
from . import oauth2


router = APIRouter(
    prefix="/posts",
    tags=["posts"]
)

@router.get('', status_code=status.HTTP_200_OK, response_model=list[schemas.PostResponse])
def get_posts(
    db_raw: tuple = Depends(get_raw_db),
    get_current_user: models.User = Depends(oauth2.get_current_user)
):
    conn, cur = db_raw
    cur.execute(
        'SELECT p.id, p.title, p.content, p.published, p.created_at, p.user_id, '
        'u.email AS user_email, u.created_at AS user_created_at '
        'FROM posts p JOIN users u ON p.user_id = u.id WHERE p.user_id = %s',
        (get_current_user.id,)
    )
    posts = cur.fetchall()
    
    formatted_posts = []
    for post in posts:
        formatted_posts.append({
            "id": post["id"],
            "title": post["title"],
            "content": post["content"],
            "published": bool(post["published"]),
            "created_at": post["created_at"],
            "user_id": post["user_id"],
            "owner": {
                "id": post["user_id"],
                "email": post["user_email"],
                "created_at": post["user_created_at"]
            }
        })
    
    return formatted_posts


@router.get('/orm', status_code=status.HTTP_200_OK,response_model=list[schemas.PostOut])
def get_posts_orm(
    db: Session = Depends(get_db),
    get_current_user: models.User = Depends(oauth2.get_current_user),
    limit: int = 10,
    skip: int = 0,  
    search: Optional[str] = ""
):
    posts = db.query(models.Post).filter(models.Post.title.contains(search)).offset(skip).limit(limit).all()
    results = db.query(models.Post, func.count(models.Vote.post_id).label("votes")).join(models.Vote, models.Vote.post_id == models.Post.id, isouter=True).group_by(models.Post.id).filter(models.Post.title.contains(search)).offset(skip).limit(limit).all()

    return results


@router.post('', status_code=status.HTTP_201_CREATED, response_model=schemas.MessageResponse)
def create_item(
    item: schemas.Post,
    db_raw: tuple = Depends(get_raw_db),
    get_current_user: models.User = Depends(oauth2.get_current_user)
):
    conn, cur = db_raw
    cur.execute(
        'INSERT INTO posts (title, content, published, user_id) VALUES (%s, %s, %s, %s)',
        (item.title, item.content, item.published, get_current_user.id)
    )
    conn.commit()
    return {"message": "Post created successfully"}

@router.post('/orm', status_code=status.HTTP_201_CREATED, response_model=schemas.CreatePostResponse)
def create_post_orm(
    item: schemas.Post,
    db: Session = Depends(get_db),
    get_current_user: models.User = Depends(oauth2.get_current_user),
):
    new_post = models.Post(**item.model_dump())
    new_post.user_id = get_current_user.id
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return {"message": "Post created successfully", "post": new_post}


@router.get('/{id}', status_code=status.HTTP_200_OK, response_model=schemas.SinglePostResponse)
def get_post(
    id: int,
    db_raw: tuple = Depends(get_raw_db),
    get_current_user: models.User = Depends(oauth2.get_current_user)
):
    conn, cur = db_raw
    cur.execute(
        'SELECT p.id, p.title, p.content, p.published, p.created_at, p.user_id, '
        'u.email AS user_email, u.created_at AS user_created_at '
        'FROM posts p JOIN users u ON p.user_id = u.id WHERE p.id = %s',
        (id,)
    )
    post = cur.fetchone()
    if post:
        formatted_post = {
            "id": post["id"],
            "title": post["title"],
            "content": post["content"],
            "published": bool(post["published"]),
            "created_at": post["created_at"],
            "user_id": post["user_id"],
            "owner": {
                "id": post["user_id"],
                "email": post["user_email"],
                "created_at": post["user_created_at"]
            }
        }
        return {'success': True, 'response': formatted_post}
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={'success': False, 'response': f'id:{id} not found'}
    )

@router.get('/orm/{id}', status_code=status.HTTP_200_OK, response_model=schemas.SinglePostResponse)
def get_post_orm(
    id: int,
    db: Session = Depends(get_db),
    get_current_user: models.User = Depends(oauth2.get_current_user)
):
    post = db.query(models.Post).filter(models.Post.id == id).first()
    if post:
        return {'success': True, 'response': post}
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={'success': False, 'response': f'id:{id} not found'}
    )

@router.delete('/{id}', response_model=schemas.ActionResponse)
def delete_post(
    id: int,
    db_raw: tuple = Depends(get_raw_db),
    get_current_user: models.User = Depends(oauth2.get_current_user)
):
    conn, cur = db_raw
    cur.execute('SELECT * FROM posts WHERE id = %s', (id,))
    post = cur.fetchone()
    if not post:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "success": False,
                "message": f"Post with id {id} not found"
            }
        )
    if post['user_id'] != get_current_user.id:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "success": False,
                "message": "You are not authorized to delete this post"
            }
        )
    cur.execute('DELETE FROM posts WHERE id = %s', (id,))
    conn.commit()
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": f"Post with id {id} deleted successfully"
        }
    )

@router.delete('/orm/{id}', response_model=schemas.ActionResponse)
def delete_post_orm(
    id: int,
    db: Session = Depends(get_db),
    get_current_user: models.User = Depends(oauth2.get_current_user)
):
    post = db.query(models.Post).filter(models.Post.id == id).first()

    if not post:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "success": False,
                "message": f"Post with id {id} not found"
            }
        )
    if post.user_id != get_current_user.id:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "success": False,
                "message": "You are not authorized to delete this post"
            }
        )
    db.delete(post)
    db.commit()
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": f"Post with id {id} deleted successfully"
        }
    )
    

@router.put('/{id}', response_model=schemas.ActionResponse)
def update_post(
    id: int,
    item: schemas.Post,
    db_raw: tuple = Depends(get_raw_db),
    get_current_user: models.User = Depends(oauth2.get_current_user)
):
    conn, cur = db_raw
    cur.execute('SELECT * FROM posts WHERE id = %s', (id,))
    post = cur.fetchone()
    if not post:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "success": False,
                "message": f"Post with id {id} not found"
            }
        )
    if post['user_id'] != get_current_user.id:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "success": False,
                "message": "You are not authorized to update this post"
            }
        )

    cur.execute(
        'UPDATE posts SET title = %s, content = %s, published = %s WHERE id = %s',
        (item.title, item.content, item.published, id)
    )
    conn.commit()
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": f"Post with id {id} updated successfully"
        }
    )


@router.put('/orm/{id}', response_model=schemas.ActionResponse)
def update_post_orm(
    id: int,
    item: schemas.Post,
    db: Session = Depends(get_db),
    get_current_user: models.User = Depends(oauth2.get_current_user)
):
    post_querry = db.query(models.Post).filter(models.Post.id == id)
    post = post_querry.first()
    if not post:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "success": False,
                "message": f"Post with id {id} not found"
            }
        )
    if post.user_id != get_current_user.id:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "success": False,
                "message": "You are not authorized to update this post"
            }
        )
    post_querry.update(item.model_dump(), synchronize_session=False)
    db.commit()
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": f"Post with id {id} updated successfully"
        }
    )
