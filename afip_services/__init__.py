"""afip-services — Python client for AFIP/ARCA SOAP web services (WSAA + WSN).

The service catalog is defined in ``services.yaml`` inside the package. To
add a new padron-family service, edit that YAML (or ship your own via the
``AFIP_SERVICES_CATALOG`` env var / :func:`load_catalog`). For non-padron
services (wsfe, wsmtx, wsfexv1, …), declare a custom ``kind`` and register a
handler with :func:`register_handler` — see the registry module for details.
"""

from .afip_gateway import WSN
from .catalog import (
    ServiceConfig,
    ServiceEnvironment,
    WSNService,
    get_catalog,
    iter_services,
    load_catalog,
    reload_catalog,
)
from .logger import get_logger
from .models.ticket import TicketAutorizacion
from .registry import (
    HandlerNotRegisteredError,
    get_handler,
    list_registered_kinds,
    register_handler,
)
from .utils.exceptions import (
    AFIPAuthenticationError,
    AFIPError,
    AFIPRequestError,
)

__version__ = "0.2.0"

__all__ = [
    # Core
    "WSN",
    "WSNService",
    "__version__",
    # Catalog API
    "ServiceConfig",
    "ServiceEnvironment",
    "get_catalog",
    "iter_services",
    "load_catalog",
    "reload_catalog",
    # Registry API
    "register_handler",
    "get_handler",
    "list_registered_kinds",
    "HandlerNotRegisteredError",
    # Models / exceptions
    "TicketAutorizacion",
    "AFIPError",
    "AFIPAuthenticationError",
    "AFIPRequestError",
    # Logger
    "get_logger",
]
