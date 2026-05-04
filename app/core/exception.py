from fastapi import HTTPException


class AppException(HTTPException):
    def __init__(
            self,
            message: str,
            *args,
            **kwargs,
        ):
        super().__init__(*args, **kwargs)
        self.detail = kwargs.get("detail")
        self.message = message

    def __str__(self) -> str:
        return f"{self.status_code}: {self.message}: {self.detail}"

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        return f"{class_name}(status_code={self.status_code!r}, message={self.message!r}, detail={self.detail!r})"
