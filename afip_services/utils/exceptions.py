class AFIPError(Exception):
    """
    Base exception for errors related to the AFIP service.

    Attributes:
        message (str): Detailed description of the error.
        code (int, optional): Numeric code identifying the error.
        inner_exception (Exception, optional): Original exception that caused the error.
    """

    def __init__(
        self,
        message: str,
        code: int | None = None,
        inner_exception: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.inner_exception = inner_exception

    def __str__(self) -> str:
        base = f"[{self.code}] " if self.code is not None else ""
        return f"{base}{self.message}"


class AFIPAuthenticationError(AFIPError):
    """
    Error authenticating with the AFIP service.
    May be raised when certificate loading, TRA signing, or the authentication response fails.
    """

    pass


class AFIPRequestError(AFIPError):
    """
    Error when making a request to the AFIP service.
    Used when there are issues with communication or processing of the service response.
    """

    pass
