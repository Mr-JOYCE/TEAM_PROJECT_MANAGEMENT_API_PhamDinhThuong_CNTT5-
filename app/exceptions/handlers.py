from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException
):
    status_code = exc.status_code

    if status_code == 400:
        code = "BAD_REQUEST"
        message = "Bad request"

    elif status_code == 403:
        code = "FORBIDDEN"
        message = "Permission denied"

    elif status_code == 404:
        code = "NOT_FOUND"
        message = "Resource not found"

    else:
        code = "HTTP_ERROR"
        message = str(exc.detail)

    return JSONResponse(
        status_code=status_code,
        content={
            "status": status_code,
            "code": code,
            "message": message,
            "detail": exc.detail
        }
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
):
    return JSONResponse(
        status_code=422,
        content={
            "status": 422,
            "code": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "detail": exc.errors()
        }
    )