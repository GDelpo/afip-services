"""afip-services — Python client for AFIP/ARCA SOAP web services (WSAA + WSN)."""

from .afip_config import WSNService
from .afip_gateway import WSN
from .logger import get_logger
from .models.ticket import TicketAutorizacion
from .utils.exceptions import (
    AFIPAuthenticationError,
    AFIPError,
    AFIPRequestError,
)

__version__ = "0.1.0"

__all__ = [
    "WSN",
    "WSNService",
    "TicketAutorizacion",
    "AFIPError",
    "AFIPAuthenticationError",
    "AFIPRequestError",
    "get_logger",
    "__version__",
]
