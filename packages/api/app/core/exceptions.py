from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger

logger = get_logger("app.errors")


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    # Headers on the exception are part of the contract, not decoration:
    # 429 carries Retry-After, 409 tells a checkout retry how long to back off,
    # and 401 carries WWW-Authenticate. Dropping them leaves clients guessing.
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=getattr(exc, "headers", None),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.info(
        "request rejected by validation",
        extra={"http_path": request.url.path, "error_count": len(exc.errors())},
    )
    return JSONResponse(
        status_code=422,
        content={"detail": jsonable_errors(exc), "body": jsonable_body(exc)},
    )


def jsonable_errors(exc: RequestValidationError) -> list:
    from fastapi.encoders import jsonable_encoder

    return jsonable_encoder(exc.errors())


def jsonable_body(exc: RequestValidationError):
    from fastapi.encoders import jsonable_encoder

    return jsonable_encoder(exc.body)
