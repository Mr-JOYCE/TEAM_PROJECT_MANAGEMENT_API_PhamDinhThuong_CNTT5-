from fastapi import HTTPException, status


class BadRequestException(HTTPException):
    def __init__(
        self,
        detail: str = "Bad request"
    ):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )


class ForbiddenException(HTTPException):
    def __init__(
        self,
        detail: str = "Permission denied"
    ):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class NotFoundException(HTTPException):
    def __init__(
        self,
        detail: str = "Resource not found"
    ):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )