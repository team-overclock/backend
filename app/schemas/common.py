from typing import Annotated, Literal, Union
from pydantic import Field, EmailStr, BeforeValidator
from datetime import datetime


def empty_to_none(v: str | None):
    if not v:
        return None
    return v

OptionalStr = Annotated[
    Union[str, None],
    BeforeValidator(empty_to_none)
]
OptionalEmail = Annotated[
    Union[EmailStr, None],
    BeforeValidator(empty_to_none)
]

Password = Annotated[str, Field(min_length=4)]

PK_AI = Annotated[int, Field(description="Primary Key (Auto Increment)", ge=1)]
PK_STR = Annotated[str, Field(description="Primary Key (String)", examples=["abc123"], min_length=1)]

RegionName = Annotated[str, Field(description="동네 이름", examples=["서울특별시 강남구 역삼동"])]
InfrastructureType = Annotated[str, Field(description="인프라 유형", examples=["지하철역"])]

TaskID = Annotated[PK_STR, Field(description="추천 요청을 식별하는 고유 ID")]
PropertyName = Annotated[str, Field(description="매물 이름", examples=["삼성래미안"])]
Score = Annotated[float, Field(description="추천 점수", ge=0, le=100)]
PriceUnit = Annotated[int, Field(description="단위: 원")]
Status = Annotated[Literal["completed", "in_progress", "failed"], Field(description="요청 처리 상태")]

Datetime = Annotated[datetime, Field()]
