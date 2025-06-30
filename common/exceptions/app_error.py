from fastapi import HTTPException


class AppError(Exception):
    """Base exception for all App-related Errors."""

    status_code: int = 500
    detail: str = "An unexpected error occured. Please contact support."

    def __init__(self, message: str | None = None, code: int | None = None) -> None:
        """
        Initialize the AppError.

        Args:
            message: The error message. If None, uses the default detail.
            code: The HTTP status code. If None, uses the default status_code.

        """
        self.message = message or self.detail
        self.code = code or self.status_code
        super().__init__(self.message)

    def to_http_exception(self) -> HTTPException:
        """
        Convert the AppError to an HTTPException.

        Returns:
            The corresponding HTTPException.

        """
        return HTTPException(
            status_code=self.code,
            detail={
                "message": self.message,
                "code": self.code,
            },
        )

    def __str__(self) -> str:
        """
        Return a String representation of the error.

        Returns:
            A formatted error message with stack trace.

        """
        return f"AppError: {self.message} Code: {self.code}\nStack Trace:\n{self.__traceback__}"
