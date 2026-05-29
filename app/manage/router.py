"""관리용 라우터"""

from fastapi import APIRouter

from . import tables, data, seeds


router = APIRouter(prefix="/manage", tags=["manage"])


router.include_router(tables.router)
router.include_router(data.router)
router.include_router(seeds.router)
