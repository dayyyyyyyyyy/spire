import asyncio
import base64
from datetime import datetime
import io
from app.utils.ecs_log import logger
from pydantic import UUID4
from sqlalchemy import select, and_
from app.session import Transactional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.post import Post
from app.schemas.post import ImageCreate, PostCreate, PostUpdate, CommentCreate, CommentUpdate
from app.core.exceptions.post import PostNotFoundException, CommentNotFoundException, UserNotOwnerException
from app.models.post import Comment, PostLike
from sqlalchemy.exc import IntegrityError, NoResultFound
from app.core.exceptions.base import (
    BadRequestException,
    ForbiddenException,
    NotFoundException,
)
from sqlalchemy import and_, delete, select, func, case, update
from app.repository import post
from app.repository import comment
from app.utils.aws import s3_client, bucket_name

class PostService:
    @Transactional()
    async def get_posts(self, user_id: UUID4 | None, limit: int, offset: int, session: AsyncSession):
        try:
            total, posts = await asyncio.gather(
                post.count(),
                post.get_list_with_like_cnt_comment_cnt(limit, offset, user_id),
            )

        except NoResultFound as e:
            raise NotFoundException("Posts not found") from e

        next_cursor = offset + len(posts) if total and total > offset + len(posts) else None
        return total, posts, next_cursor


    @Transactional()
    async def get_my_posts(self, user_id: UUID4, limit: int, offset: int, session: AsyncSession):
        try:
            total, posts = await asyncio.gather(
                post.count_by_user_id(user_id),
                post.get_list_with_like_cnt_comment_cnt_by_user_id(user_id, limit, offset),
            )

        except NoResultFound as e:
            raise NotFoundException("Posts not found") from e

        next_cursor = offset + len(posts) if total and total > offset + len(posts) else None
        return total, posts, next_cursor
    
    @Transactional()
    async def create_post(
        self,
        user_id: UUID4,
        post_data: PostCreate,
        session: AsyncSession,
        **kwargs
    ) -> Post:

        post_dict = post_data.create_dict(user_id)

        try:
            return await post.create(post_dict)
        
        except IntegrityError as e:
            raise BadRequestException(str(e.orig)) from e
    
    @Transactional()
    async def create_image(
        self,
        user_id: UUID4,
        post_id: UUID4,
        image_data: ImageCreate,
        session: AsyncSession,
        **kwargs
    ) -> Post:
        
        img_url = upload_post_image_to_s3(post_id, image_data.modified_image)

        image_dict = image_data.create_dict(user_id, post_id)

        try:
            await post.create_image(image_dict)
        
        except IntegrityError as e:
            raise BadRequestException(str(e.orig)) from e

        return img_url
    
    @Transactional()
    async def get_post_by_id(self, post_id: UUID4, user_id: UUID4, session: AsyncSession, **kwargs) -> Post:

        try:
            return await post.get_with_like_cnt_by_id(id=post_id, user_id=user_id)
        
        except NoResultFound as e:
            raise PostNotFoundException from e
        
    @Transactional()
    async def update_post_by_id(
        self,
        id: UUID4,
        user_id: UUID4,
        post_data: PostUpdate,
        session: AsyncSession,
        **kwargs
    ) -> Post:
        try:
            post_obj = await self.get_post_by_id(id, user_id)
        except NoResultFound as e:
            raise PostNotFoundException from e
        
        if post_obj.user_id != user_id:
            raise ForbiddenException("You are not authorized to delete this post")
        
        post_dict = post_data.create_dict()

        new_post_obj = await post.update_by_id(id, post_dict)
        new_post_obj.like_cnt = post_obj.like_cnt

        return new_post_obj

        
    @Transactional()
    async def delete_post_by_id(self, post_id: UUID4, request_user_id: UUID4, session: AsyncSession):

        try:
            post_obj = await self.get_post_by_id(post_id, request_user_id)
        except NoResultFound as e:
            raise PostNotFoundException from e
        
        if post_obj.user_id != request_user_id:
                raise ForbiddenException("You are not authorized to delete this post")

        await post.delete_by_id(post_id)

    @Transactional()
    async def toggle_post_like(
        self, post_id: UUID4, user_id: UUID4, session: AsyncSession, **kwargs
    ) -> PostLike:
        result = await session.execute(
            select(PostLike).where(
                and_(PostLike.post_id == post_id, PostLike.user_id == user_id)
            )
        )

        post_like: PostLike | None = result.scalars().first()

        if post_like is None:
            post_like = PostLike(post_id=post_id, user_id=user_id, is_liked=True)
            session.add(post_like)
            await session.commit()
            return post_like

        else:
            post_like.is_liked = not (post_like.is_liked)
            await session.commit()
            return post_like

    @Transactional()
    async def get_comments_by_post_id(self, post_id: UUID4, user_id: UUID4 | None, limit: int, offset: int, session: AsyncSession):
        try:
            total, comments = await asyncio.gather(
                comment.count_by_post_id(post_id),
                comment.get_list_with_like_cnt_by_post_id(post_id, user_id, limit, offset),
            )

        except NoResultFound as e:
            raise NotFoundException("Post not found") from e

        next_cursor = offset + len(comments) if total and total > offset + len(comments) else None
        return total, comments, next_cursor
    
    @Transactional()
    async def create_comment(
        self,
        post_id: UUID4,
        comment_data: CommentCreate,
        user_id: UUID4,
        session: AsyncSession,
        **kwargs
    ) -> Comment:
        comment_ = comment_data.dict()
        comment_["post_id"] = post_id
        comment_["user_id"] = user_id

        try:
            cmt_obj = await comment.create(comment_)
            return cmt_obj
        except IntegrityError as e:
            raise BadRequestException(str(e.orig)) from e
        
    @Transactional()
    async def update_comment_by_id(
        self,
        comment_id: UUID4,
        user_id: UUID4,
        comment_data: CommentUpdate,
        session: AsyncSession,
        **kwargs
    ) -> Comment:
        try:
            comment_obj = await comment.get_by_id(comment_id)
        except NoResultFound as e:
            raise CommentNotFoundException from e
        
        if comment_obj.user_id != user_id:
            raise ForbiddenException("You are not authorized to delete this comment")
        
        comment_dict = comment_data.dict()

        new_comment_obj = await comment.update_by_id(comment_id, comment_dict)
        new_comment_obj.like_cnt = comment_obj.like_cnt

        return new_comment_obj

    @Transactional()
    async def delete_comment_by_id(self, comment_id: UUID4, request_user_id: UUID4, session: AsyncSession) -> Comment:
        result = await session.execute(select(Comment).where(and_(Comment.id == comment_id)))

        comment: Comment | None = result.scalars().first()

        if not comment:
            raise CommentNotFoundException("Comment not found")
        
        if comment.user_id != request_user_id:
            raise UserNotOwnerException("user is not the owver")

        await session.delete(comment)
        await session.commit()
        return comment


def upload_post_image_to_s3(
    post_id: UUID4,
    image_base64: str,
    file_extension: str = "png",
    ):
    img_url = None
    try:
        image_bytes = base64.b64decode(image_base64)

        image_key = f"post_image/{post_id}/{datetime.now().strftime('%Y-%m-%d_%H:%M:%S')}"

        with io.BytesIO(image_bytes) as image_file:
        # Upload the image to the S3 bucket
            s3_client.upload_fileobj(
                image_file,
                bucket_name,
                image_key,
                ExtraArgs={
                    "ContentType": f"image/{file_extension}",
                },
            )
        
        img_url = f"https://{bucket_name}.s3.amazonaws.com/{image_key}"

    except Exception as e:
            logger.error(e)
            raise e
    
    return img_url

