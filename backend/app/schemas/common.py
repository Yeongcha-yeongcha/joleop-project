from typing import Any

from pydantic import BaseModel


class ErrorBody(BaseModel):
    code: str
    message: str


class SuccessResponse(BaseModel):
    success: bool = True
    data: Any


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorBody


def success_response(data: Any) -> dict[str, Any]:
    return {"success": True, "data": data}
