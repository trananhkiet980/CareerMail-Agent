class AppError(Exception):
    def __init__(self, message: str, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class SetupError(AppError):
    def __init__(self, missing: str, message: str) -> None:
        super().__init__(message, code="ERR_SETUP")
        self.missing = missing


class GmailError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="ERR_GMAIL")


class LLMError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="ERR_LLM")


class CareerError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="ERR_CAREER")
