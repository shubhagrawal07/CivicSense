from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class InvalidInput(Exception):
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message


def _body(detail: str, errors: list[dict]) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": detail, "errors": errors})


async def invalid_input_handler(request: Request, exc: InvalidInput):
    return _body(exc.message, [{"field": exc.field, "message": exc.message}])


async def validation_handler(request: Request, exc: RequestValidationError):
    errors = [{"field": str(e["loc"][-1]), "message": e["msg"]} for e in exc.errors()]
    return _body("Invalid request", errors)
