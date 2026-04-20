"""Handler registry for non-built-in AFIP service kinds.

Each entry in ``services.yaml`` carries a ``kind`` field (e.g. ``padron_list``).
The built-in kinds (``padron_list`` and ``padron_single``) are registered by
the gateway at import time. Any custom kind needs an external handler
registered via :func:`register_handler`.

Example — adding a handler for wsfe::

    from afip_services.registry import register_handler

    @register_handler("factura_electronica")
    def wsfe_handler(wsn, client, **kwargs):
        # wsn is the WSN gateway instance; client is the zeep client.
        # Implement the service-specific SOAP call here.
        return client.service.FECAESolicitar(...)

Handlers receive the calling ``WSN`` instance and the active ``zeep.Client``,
plus whatever keyword arguments the caller passes to ``WSN.request(**kwargs)``.
"""

from __future__ import annotations

from typing import Callable


Handler = Callable[..., object]

_HANDLERS: dict[str, Handler] = {}


def register_handler(kind: str) -> Callable[[Handler], Handler]:
    """Decorator — register a handler function for a service *kind*.

    Calling twice with the same kind overwrites the previous handler.
    """

    def decorator(fn: Handler) -> Handler:
        _HANDLERS[kind] = fn
        return fn

    return decorator


def get_handler(kind: str) -> Handler | None:
    """Return the handler registered for *kind* or ``None`` if absent."""
    return _HANDLERS.get(kind)


def list_registered_kinds() -> list[str]:
    """Return every registered kind (useful for diagnostics)."""
    return sorted(_HANDLERS.keys())


class HandlerNotRegisteredError(LookupError):
    """Raised when a service kind has no registered handler."""
