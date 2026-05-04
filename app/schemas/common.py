from typing import Annotated, Union
from pydantic import Field, EmailStr, BeforeValidator


def empty_to_none(v: str | None):
    if not v:
        return None
    return v

UserName = Annotated[str, Field(min_length=1)]
Password = Annotated[str, Field(min_length=4)]
OptionalEmail = Annotated[
    Union[EmailStr, None],
    BeforeValidator(empty_to_none)
]

RegionName = Annotated[str, Field(description="동네 이름", examples=["서울특별시 강남구 역삼동"])]
InfrastructureType = Annotated[str, Field(description="인프라 유형", examples=["지하철역"])]
