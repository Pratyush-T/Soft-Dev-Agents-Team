"""API v1 Router aggregating all domain sub-routers."""
from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.connections import router as connections_router
from app.api.v1.posts import router as posts_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.messages import router as messages_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.uploads import router as uploads_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(auth_router)
api_v1_router.include_router(users_router)
api_v1_router.include_router(connections_router)
api_v1_router.include_router(posts_router)
api_v1_router.include_router(jobs_router)
api_v1_router.include_router(messages_router)
api_v1_router.include_router(notifications_router)
api_v1_router.include_router(uploads_router)

__all__ = ["api_v1_router"]
