"""관리용 라우터"""

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from ...database import get_db
from ...models import Region, Property, Infrastructure
from ..schemas import BackgroundSuccessResponse, DataDownloadStatusResponse, DataInsertStatusResponse

from .insert import run as insert
from .download import run as download
from .download import get_current_version, get_downloading_version


router = APIRouter(prefix="/data")


@router.post(
    "/sources",
    summary="소스 데이터 파일 다운로드",
    status_code=status.HTTP_202_ACCEPTED,
)
def download_data(
    background_tasks: BackgroundTasks,
) -> BackgroundSuccessResponse:
    """구글 드라이브 내 소스 데이터 파일을 다운로드"""

    background_tasks.add_task(
        download,
        silent=False,
    )

    return {
        "requested": True,
    }

@router.get(
    "/sources/status",
    summary="다운로드 상태 확인",
    status_code=status.HTTP_200_OK,
)
def download_data(
) -> DataDownloadStatusResponse:
    """구글 드라이브 내 소스 데이터 파일을 다운로드"""

    curr_version = get_current_version()
    downloading_version = get_downloading_version()

    return {
        "curr_version": curr_version,
        "downloading_version": downloading_version,
    }


@router.patch(
    "",
    summary="데이터 삽입",
    status_code=status.HTTP_202_ACCEPTED,
)
def insert_data(
    background_tasks: BackgroundTasks,
) -> BackgroundSuccessResponse:
    """다운로드된 소스 데이터 파일을 읽어 데이터베이스에 삽입"""

    background_tasks.add_task(
        insert,
        silent=False,
    )

    return {
        "requested": True,
    }

@router.get(
    "/status",
    summary="데이터 삽입 상태 확인",
    status_code=status.HTTP_200_OK,
)
def check_data_status(
    db: Session = Depends(get_db),
) -> DataInsertStatusResponse:
    """데이터 삽입 상태 확인"""

    result = db.execute(
        select(
            exists().where(Region.id),
            exists().where(Property.id),
            exists().where(Infrastructure.id),
        ),
    ).tuples().first()

    return {
        "has_region": result[0],
        "has_property": result[1],
        "has_infrastructure": result[2],
    }
