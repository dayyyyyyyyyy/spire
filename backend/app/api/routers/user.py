from typing_extensions import Annotated
from fastapi import APIRouter, Depends, Form, Query, Request
from pydantic import Json, UUID4
from app.core.exceptions.base import BadRequestException
from app.core.fastapi.dependency.permission import (
    AllowAll,
    IsAuthenticated,
    PermissionDependency,
)
from app.schemas.user import (
    CheckUserInfoResponse,
    LoginRequest,
    LoginResponse,
    UserCreate,
)
from app.session import get_db_transactional_session
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.user_service import UserService
from app.utils.pagination import limit_offset_query


user_router = APIRouter()

@user_router.post(
    "/{user_id}/follow_request",
    summary="Request user follow",
    description="Request user follow",
    dependencies=[Depends(PermissionDependency([IsAuthenticated]))],
)
async def request_follow(
    req: Request,
    user_id: UUID4,
):
    user_svc = UserService()
    follow = await user_svc.request_follow(
        followed_user_id=user_id, 
        following_user_id = req.user.id
    )
    return {"message": f"Requested user {user_id} follow"}

@user_router.delete(
    "/{user_id}/cancel_request",
    summary="Cancel user follow request",
    description="Cancel user follow request",
    dependencies=[Depends(PermissionDependency([IsAuthenticated]))],
)
async def cancel_follow_request(
    req: Request,
    user_id: UUID4,
):
    user_svc = UserService()
    follow = await user_svc.delete_follow(
        followed_user_id=user_id, 
        following_user_id=req.user.id, 
        accept_status=0
    )
    return {"message": f"Canceled user {user_id} follow request"}

@user_router.post(
    "/{user_id}/accept_request",
    summary="Accept user follow request",
    description="Accept user follow request",
    dependencies=[Depends(PermissionDependency([IsAuthenticated]))],
)
async def accept_follow_request(
    req: Request,
    user_id: UUID4,
):
    user_svc = UserService()
    follow = await user_svc.accept_follow_request(
        followed_user_id=req.user.id,
        following_user_id=user_id
    )
    return {"message": f"Accepted user {user_id} follow request"}

@user_router.delete(
    "/{user_id}/reject_request",
    summary="Reject user follow request",
    description="Reject user follow request",
    dependencies=[Depends(PermissionDependency([IsAuthenticated]))],
)
async def reject_follow_request(
    req: Request,
    user_id: UUID4,
):
    user_svc = UserService()
    follow = await user_svc.delete_follow(
        followed_user_id=req.user.id,
        following_user_id=user_id,
        accept_status=0
    )
    return {"message": f"Rejected user {user_id} follow request"}

@user_router.delete(
    "/{user_id}/unfollow",
    summary="Unfollow user",
    description="Unfollow user",
    dependencies=[Depends(PermissionDependency([IsAuthenticated]))],
)
async def unfollow(
    req: Request,
    user_id: UUID4,
):
    user_svc = UserService()
    follow = await user_svc.delete_follow(
        followed_user_id=user_id, 
        following_user_id=req.user.id,
        accept_status=1
    )
    return {"message": f"Unfollowed user {user_id}"}

@user_router.delete(
    "/{user_id}/reject_follow",
    summary="Reject user follow",
    description="Reject user follow",
    dependencies=[Depends(PermissionDependency([IsAuthenticated]))],
)
async def reject_follow(
    req: Request,
    user_id: UUID4,
):
    user_svc = UserService()
    follow = await user_svc.delete_follow(
        followed_user_id=req.user.id,
        following_user_id=user_id,
        accept_status=1
    )
    return {"message": f"Rejected user {user_id} follow"}

@user_router.get(
    "/{user_id}/followers",
    summary="Get user followers",
    description="Get user followers",
    dependencies=[Depends(PermissionDependency([AllowAll]))],
)
async def get_followers(
    user_id: UUID4,
    pagination: dict = Depends(limit_offset_query)
):
    user_svc = UserService()
    total, items, next_cursor = await user_svc.get_followers(
        user_id=user_id, **pagination
    )
    return {"total": total, "items": items, "next_cursor": next_cursor}

@user_router.get(
    "/{user_id}/followings",
    summary="Get user followings",
    description="Get user followings",
    dependencies=[Depends(PermissionDependency([AllowAll]))],
)
async def get_followings(
    user_id: UUID4,
    pagination: dict = Depends(limit_offset_query)
):
    user_svc = UserService()
    total, items, next_cursor = await user_svc.get_followings(
        user_id=user_id, **pagination
    )
    return {"total": total, "items": items, "next_cursor": next_cursor}