"""관리용 라우터"""

from fastapi import APIRouter

from . import seeds


router = APIRouter(prefix="/manage", tags=["manage"])

router.include_router(seeds.router)
