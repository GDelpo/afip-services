"""Backwards-compatible module.

The service catalog used to be a hand-coded :class:`Enum` in this file.
It now lives in ``services.yaml`` and is built dynamically by
:mod:`afip_services.catalog`. This module re-exports the public symbols so
existing imports such as ``from afip_services.afip_config import WSNService``
keep working.
"""

from .catalog import (
    ServiceConfig,
    ServiceEnvironment,
    WSNService,
    get_catalog,
    iter_services,
    load_catalog,
    reload_catalog,
)

__all__ = [
    "ServiceConfig",
    "ServiceEnvironment",
    "WSNService",
    "get_catalog",
    "iter_services",
    "load_catalog",
    "reload_catalog",
]
