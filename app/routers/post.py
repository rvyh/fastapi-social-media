from fastapi import Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from typing import List

from .. import models, schemas, oauth2
from ..database import get_db

router = APIRouter(
    prefix="/posts",
    tags=['Posts']
)


@router.get("/", response_model=List[schemas.Post])
def get_posts(db: Session = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    posts = db.query(models.Post).all()
    return posts


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.Post)
def create_posts(
        post: schemas.PostCreate,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(oauth2.get_current_user)
):
    new_post = models.Post(owner_id=current_user.id, **post.dict())
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post


@router.get("/{post_id}", response_model=schemas.Post)
def get_post(
        post_id: int,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(oauth2.get_current_user)
):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Post with id: {post_id} was not found")

    return post


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
        post_id: int,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(oauth2.get_current_user)
):
    post_query = db.query(models.Post).filter(models.Post.id == post_id)
    post = post_query.first()

    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Post with id: {post_id} does not exist")

    if post.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not authorized to perform requested action.")

    post_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{post_id}", response_model=schemas.Post)
def update_post(
        post_id: int,
        new_post: schemas.PostCreate,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(oauth2.get_current_user)
):
    post_query = db.query(models.Post).filter(models.Post.id == post_id)
    post = post_query.first()

    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Post with id: {post_id} does not exist")

    if post.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not authorized to perform requested action.")

    post_query.update(new_post.dict(), synchronize_session=False)
    db.commit()
    return post_query.first()
