from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppException(HTTPException):
    def __init__(
        self,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        detail: str = "Request could not be processed.",
        code: str = "INVALID_REQUEST",
    ) -> None:
        self.error_code = code
        super().__init__(status_code=status_code, detail=detail)


class UnauthorizedException(AppException):
    def __init__(self, detail: str = "인증이 필요합니다.") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            code="UNAUTHORIZED",
        )


class ForbiddenException(AppException):
    def __init__(self, detail: str = "접근 권한이 없습니다.") -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            code="FORBIDDEN",
        )


class InvalidProfilePasswordException(AppException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="비밀번호가 올바르지 않습니다.",
            code="INVALID_PROFILE_PASSWORD",
        )


class OnboardingAlreadyCompletedException(AppException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 온보딩을 완료했습니다.",
            code="ONBOARDING_ALREADY_COMPLETED",
        )


class InvalidCourseStateException(AppException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="현재 코스 상태에서 수행할 수 없는 요청입니다.",
            code="INVALID_COURSE_STATE",
        )


class AttemptRequiredException(AppException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="다음 단계로 이동하려면 먼저 시도가 필요합니다.",
            code="ATTEMPT_REQUIRED",
        )


class AudioValidationException(AppException):
    def __init__(self, *, code: str, detail: str) -> None:
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
        self.error_code = code


class AccessTokenExpiredException(UnauthorizedException):
    def __init__(self) -> None:
        super().__init__("access token이 만료되었습니다.")
        self.error_code = "ACCESS_TOKEN_EXPIRED"


class InvalidRefreshTokenException(UnauthorizedException):
    def __init__(self) -> None:
        super().__init__("유효하지 않은 refresh token입니다.")
        self.error_code = "INVALID_REFRESH_TOKEN"


class InvalidParentCredentialsException(UnauthorizedException):
    def __init__(self) -> None:
        super().__init__("아이디 또는 비밀번호가 올바르지 않습니다.")
        self.error_code = "INVALID_PARENT_CREDENTIALS"


class ParentUsernameAlreadyExistsException(AppException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 사용 중인 아이디입니다.",
            code="PARENT_USERNAME_ALREADY_EXISTS",
        )


class ParentNotFoundException(AppException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="부모 계정을 찾을 수 없습니다.",
            code="PARENT_NOT_FOUND",
        )


class ProfileNotFoundException(AppException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="프로필을 찾을 수 없습니다.",
            code="PROFILE_NOT_FOUND",
        )


class ProfileLimitExceededException(AppException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="프로필은 최대 5개까지 만들 수 있습니다.",
            code="PROFILE_LIMIT_EXCEEDED",
        )


class BookNotFoundException(AppException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="책을 찾을 수 없습니다.",
            code="BOOK_NOT_FOUND",
        )


class BookLockedException(AppException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="잠긴 책입니다.",
            code="BOOK_LOCKED",
        )


class SessionNotFoundException(AppException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="학습 세션을 찾을 수 없습니다.",
            code="SESSION_NOT_FOUND",
        )


class SessionAccessDeniedException(ForbiddenException):
    def __init__(self) -> None:
        super().__init__("해당 학습 세션에 접근할 수 없습니다.")
        self.error_code = "SESSION_ACCESS_DENIED"


class SessionAlreadyCompletedException(AppException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 완료된 학습 세션입니다.",
            code="SESSION_ALREADY_COMPLETED",
        )


class InvalidStepException(AppException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="현재 학습 단계가 일치하지 않습니다.",
            code="INVALID_STEP",
        )


class QuestionNotFoundException(AppException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="학습 문제를 찾을 수 없습니다.",
            code="QUESTION_NOT_FOUND",
        )


class ResultNotAvailableException(AppException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="아직 결과를 조회할 수 없습니다.",
            code="RESULT_NOT_AVAILABLE",
        )


def error_payload(code: str, message: str) -> dict:
    return {"success": False, "error": {"code": code, "message": message}}


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc, AppException):
        code = exc.error_code
    elif exc.status_code == status.HTTP_401_UNAUTHORIZED:
        code = "UNAUTHORIZED"
    elif exc.status_code == status.HTTP_403_FORBIDDEN:
        code = "FORBIDDEN"
    elif exc.status_code == status.HTTP_404_NOT_FOUND:
        code = "NOT_FOUND"
    elif exc.status_code == status.HTTP_409_CONFLICT:
        code = "CONFLICT"
    else:
        code = "ERROR"
    message = exc.detail if isinstance(exc.detail, str) else "요청을 처리할 수 없습니다."
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload(code, message),
        headers=getattr(exc, "headers", None),
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_payload("INVALID_REQUEST", "요청 값이 올바르지 않습니다."),
    )
