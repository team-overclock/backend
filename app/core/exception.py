import enum
from fastapi import HTTPException

from .enums import AppErrorCodeEnum


class AppException(HTTPException):
    def __init__(
            self,
            message: str,
            *args,
            **kwargs,
        ):
        code = kwargs.get("error_code") or kwargs.get("code") or AppErrorCodeEnum.UNKNOWN_ERROR
        if "error_code" in kwargs: del kwargs["error_code"]
        if "code" in kwargs: del kwargs["code"]

        super().__init__(*args, **kwargs)
        self.code = code.value if isinstance(code, enum.Enum) else code
        self.detail = kwargs.get("detail")
        self.message = message

    def __str__(self) -> str:
        return f"{self.status_code}: {self.message}: {self.detail}"

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        return f"{class_name}(status_code={self.status_code!r}, message={self.message!r}, detail={self.detail!r})"
