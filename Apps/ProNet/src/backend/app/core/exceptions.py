"""Domain exceptions and standardized error response mapping."""
from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class ProNetException(HTTPException):
    """Base domain exception with standardized error structure."""
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(status_code=status_code, detail=message)
        self.code = code
        self.message = message
        self.details = details or {}


class InvalidCredentialsException(ProNetException):
    def __init__(self, message: str = "Invalid email address or password."):
        super().__init__(
            code="INVALID_CREDENTIALS",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class TokenExpiredException(ProNetException):
    def __init__(self, message: str = "Your authentication token has expired. Please log in again."):
        super().__init__(
            code="TOKEN_EXPIRED",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class InvalidTokenException(ProNetException):
    def __init__(self, message: str = "Invalid or malformed authentication token."):
        super().__init__(
            code="INVALID_TOKEN",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class UnauthorizedException(ProNetException):
    def __init__(self, message: str = "Authentication required to access this resource."):
        super().__init__(
            code="UNAUTHORIZED",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class NotJobOwnerException(ProNetException):
    def __init__(self, message: str = "You are not authorized to view applicants for this job posting."):
        super().__init__(
            code="NOT_JOB_OWNER",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
        )


class MustBeFirstDegreeException(ProNetException):
    def __init__(self, message: str = "Direct messaging is restricted to confirmed 1st-degree connections."):
        super().__init__(
            code="MUST_BE_FIRST_DEGREE",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
        )


class CannotModerateCommentException(ProNetException):
    def __init__(self, message: str = "You do not have permission to delete this comment."):
        super().__init__(
            code="CANNOT_MODERATE_COMMENT",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
        )


class ResourceNotFoundException(ProNetException):
    def __init__(self, message: str = "The requested resource could not be found."):
        super().__init__(
            code="RESOURCE_NOT_FOUND",
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
        )


class UserNotFoundException(ProNetException):
    def __init__(self, message: str = "The specified user account does not exist."):
        super().__init__(
            code="USER_NOT_FOUND",
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
        )


class PostNotFoundException(ProNetException):
    def __init__(self, message: str = "The specified feed post does not exist or has been removed."):
        super().__init__(
            code="POST_NOT_FOUND",
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
        )


class JobNotFoundException(ProNetException):
    def __init__(self, message: str = "The specified job listing does not exist."):
        super().__init__(
            code="JOB_NOT_FOUND",
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
        )


class ConnectionAlreadyRequestedException(ProNetException):
    def __init__(self, message: str = "A connection request is already pending between these users.", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            code="CONNECTION_ALREADY_REQUESTED",
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details=details,
        )


class AlreadyConnectedException(ProNetException):
    def __init__(self, message: str = "You are already connected with this professional."):
        super().__init__(
            code="ALREADY_CONNECTED",
            message=message,
            status_code=status.HTTP_409_CONFLICT,
        )


class AlreadyAppliedToJobException(ProNetException):
    def __init__(self, message: str = "You have already submitted an application for this role."):
        super().__init__(
            code="ALREADY_APPLIED_TO_JOB",
            message=message,
            status_code=status.HTTP_409_CONFLICT,
        )


class CannotWithdrawAcceptedConnectionException(ProNetException):
    def __init__(self, message: str = "Cannot withdraw a connection that has already been accepted."):
        super().__init__(
            code="CANNOT_WITHDRAW_ACCEPTED_CONNECTION",
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class SelfConnectionForbiddenException(ProNetException):
    def __init__(self, message: str = "You cannot establish a professional connection with yourself."):
        super().__init__(
            code="SELF_CONNECTION_FORBIDDEN",
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


class PayloadTooLargeException(ProNetException):
    def __init__(self, message: str = "Uploaded file exceeds maximum allowed size."):
        super().__init__(
            code="PAYLOAD_TOO_LARGE",
            message=message,
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        )


class UnsupportedMediaTypeException(ProNetException):
    def __init__(self, message: str = "File format is invalid or corrupted. Only JPEG, PNG, WEBP, PDF, and DOCX are allowed."):
        super().__init__(
            code="UNSUPPORTED_MEDIA_TYPE",
            message=message,
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        )


class MaxCommentDepthExceededException(ProNetException):
    def __init__(self, message: str = "Comments cannot be nested more than two levels deep."):
        super().__init__(
            code="MAX_COMMENT_DEPTH_EXCEEDED",
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


class EndDateBeforeStartDateException(ProNetException):
    def __init__(self, message: str = "End date cannot precede the start date."):
        super().__init__(
            code="END_DATE_BEFORE_START_DATE",
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


class SalaryMaxMustExceedMinException(ProNetException):
    def __init__(self, message: str = "Maximum salary must be greater than or equal to minimum salary."):
        super().__init__(
            code="SALARY_MAX_MUST_EXCEED_MIN",
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


class DatabaseLockedException(ProNetException):
    def __init__(self, message: str = "System is currently busy. Please retry your request in a few moments."):
        super().__init__(
            code="DATABASE_LOCKED",
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
