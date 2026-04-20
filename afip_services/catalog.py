"""Service catalog loader.

Loads the YAML catalog that describes the AFIP services this package can
talk to. Ships with a default `services.yaml` inside the package; can be
overridden by setting the ``AFIP_SERVICES_CATALOG`` env var or calling
:func:`load_catalog` at runtime.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from importlib import resources
from pathlib import Path
from typing import Iterable

import yaml


@dataclass(frozen=True)
class ServiceEnvironment:
    """URLs for a single environment (testing or production)."""

    service_url: str
    wsdl_url: str


@dataclass(frozen=True)
class ServiceConfig:
    """Static configuration for one AFIP service entry."""

    testing: ServiceEnvironment
    production: ServiceEnvironment
    service_name: str      # used to create the TRA XML for WSAA
    method_name: str       # remote method invoked on the SOAP endpoint
    kind: str              # dispatch key used by the handler registry

    def get_environment(self, is_production: bool) -> ServiceEnvironment:
        return self.production if is_production else self.testing

    def get_service_name(self) -> str:
        return self.service_name

    def get_method_name(self) -> str:
        return self.method_name


def _default_catalog_path() -> Path:
    """Return the path to the packaged default services.yaml."""
    return Path(resources.files("afip_services").joinpath("services.yaml"))


def _read_yaml(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _build_config(entry: dict) -> ServiceConfig:
    return ServiceConfig(
        testing=ServiceEnvironment(
            service_url=entry["testing_service_url"],
            wsdl_url=entry["testing_wsdl_url"],
        ),
        production=ServiceEnvironment(
            service_url=entry["production_service_url"],
            wsdl_url=entry["production_wsdl_url"],
        ),
        service_name=entry["service_name"],
        method_name=entry["method_name"],
        kind=entry.get("kind", "padron_list"),
    )


def load_catalog(path: str | os.PathLike | None = None) -> dict[str, ServiceConfig]:
    """Load a catalog YAML file. If *path* is None, look up the env var and
    fall back to the packaged default.

    Returns a dict keyed by service name (e.g. ``WS_SR_PADRON_A13``).
    """
    if path is None:
        env_path = os.getenv("AFIP_SERVICES_CATALOG")
        path = Path(env_path) if env_path else _default_catalog_path()
    raw = _read_yaml(Path(path))
    services = raw.get("services", {}) or {}
    return {name: _build_config(entry) for name, entry in services.items()}


# Loaded once at import time. Callers who want to re-load with a different
# catalog can import `reload_catalog`.
_CATALOG: dict[str, ServiceConfig] = load_catalog()


def reload_catalog(path: str | os.PathLike | None = None) -> None:
    """Replace the in-memory catalog and rebuild :class:`WSNService`."""
    global _CATALOG, WSNService
    _CATALOG = load_catalog(path)
    WSNService = _build_enum(_CATALOG)


def get_catalog() -> dict[str, ServiceConfig]:
    """Return the current in-memory catalog."""
    return dict(_CATALOG)


def iter_services() -> Iterable[tuple[str, ServiceConfig]]:
    return _CATALOG.items()


# -- Build a dynamic Enum so consumer code can still do
#    ``WSNService.WS_SR_PADRON_A13`` just like before the refactor.
def _build_enum(catalog: dict[str, ServiceConfig]) -> type[Enum]:
    # ``Enum(name, members)`` functional form. Members map directly to their
    # ``ServiceConfig`` instance, preserving ``.value.service_name``, etc.
    cls = Enum("WSNService", {name: cfg for name, cfg in catalog.items()})  # type: ignore[arg-type]

    # Re-attach the convenience methods the original Enum had.
    def _get_environment(self, is_production: bool):
        return self.value.get_environment(is_production)

    def _get_service_name(self):
        return self.value.get_service_name()

    def _get_method_name(self):
        return self.value.get_method_name()

    cls.get_environment = _get_environment  # type: ignore[attr-defined]
    cls.get_service_name = _get_service_name  # type: ignore[attr-defined]
    cls.get_method_name = _get_method_name  # type: ignore[attr-defined]

    return cls


WSNService = _build_enum(_CATALOG)
