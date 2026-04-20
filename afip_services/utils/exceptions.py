class AFIPError(Exception):
    """
    Excepción base para errores relacionados con el servicio AFIP.

    Atributos:
        message (str): Descripción detallada del error.
        code (int, opcional): Código numérico que identifica el error.
        inner_exception (Exception, opcional): Excepción original que generó el error.
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
    Error al autenticar con el servicio AFIP.
    Puede lanzarse cuando falla la carga de certificados, la firma del TRA o la respuesta de autenticación.
    """

    pass


class AFIPRequestError(AFIPError):
    """
    Error al realizar la solicitud al servicio AFIP.
    Se utiliza cuando hay problemas en la comunicación o en el procesamiento de la respuesta del servicio.
    """

    pass
