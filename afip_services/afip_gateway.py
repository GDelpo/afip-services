"""WSN gateway — orchestrates WSAA authentication + SOAP calls to AFIP.

The business logic for the padron family ships as built-in handlers
(``padron_list``, ``padron_single``). Extra service kinds are dispatched
through the handler registry — see :mod:`afip_services.registry`.
"""

from __future__ import annotations

import zeep

from .catalog import WSNService
from .logger import get_logger
from .registry import (
    HandlerNotRegisteredError,
    get_handler,
    list_registered_kinds,
    register_handler,
)
from .services.wsaa_client import WSAAClient

logger = get_logger(__name__)


class WSN:
    """High-level client that owns WSAA auth + dispatches service calls."""

    def __init__(
        self,
        service: WSNService,
        cert_path: str,
        key_path: str,
        is_production: bool = True,
        passphrase: str | None = None,
    ):
        """
        Args:
            service: member of :class:`WSNService` describing the target service.
            cert_path: path to the AFIP certificate.
            key_path: path to the private key matching the certificate.
            is_production: if True, use the production environment.
            passphrase: optional passphrase for the private key.
        """
        self.service = service
        service_config = service.value
        self.wsaa_client = WSAAClient(
            service_config.service_name, cert_path, key_path, is_production, passphrase
        )
        self.authorization_ticket = None

    # -------- auth --------

    def obtain_authorization_ticket(self):
        """Obtain a fresh WSAA authorization ticket."""
        logger.info("Obtaining authorization ticket...")
        self.wsaa_client.authenticate()
        self.authorization_ticket = self.wsaa_client.get_authorization_ticket()

    def _ensure_ticket(self):
        if not self.authorization_ticket or not self.authorization_ticket.is_valid():
            self.obtain_authorization_ticket()

    # -------- SOAP operations --------

    def get_wsn_url(self) -> str:
        """WSDL URL for the current service in the current environment."""
        env = self.service.get_environment(self.wsaa_client.is_production)
        return env.wsdl_url

    def _new_client(self) -> zeep.Client:
        return zeep.Client(wsdl=self.get_wsn_url())

    def request_afip_dummy(self) -> bool:
        """Ping the service's ``dummy`` method to verify reachability."""
        wsdl_url = self.get_wsn_url()
        logger.info(f"Requesting AFIP dummy using WSDL: {wsdl_url}")
        client = zeep.Client(wsdl=wsdl_url)
        try:
            response = client.service.dummy()
            return (
                response["appserver"] == "OK"
                and response["authserver"] == "OK"
                and response["dbserver"] == "OK"
            )
        except Exception as e:
            logger.exception("Error in AFIP dummy")
            raise RuntimeError(f"Error when calling AFIP service: {str(e)}")

    def request_persona_list(self, persona_ids: list) -> list:
        """Query a padron-family service for a list of personas.

        Dispatches through the kind-handler registry. Built-in kinds
        ``padron_list`` and ``padron_single`` are registered below.
        """
        self._ensure_ticket()
        client = self._new_client()
        kind = self.service.value.kind

        handler = get_handler(kind)
        if handler is None:
            raise HandlerNotRegisteredError(
                f"Service '{self.service.name}' declares kind '{kind}' but no "
                f"handler is registered. Register one with "
                f"@register_handler('{kind}'). "
                f"Registered kinds: {list_registered_kinds()}."
            )

        try:
            return handler(self, client, persona_ids=persona_ids)
        except HandlerNotRegisteredError:
            raise
        except Exception as e:
            logger.exception("Error in request_persona_list")
            raise RuntimeError(f"Error when calling AFIP service: {str(e)}")

    # Alias — generic entry point for future callers.
    def request(self, **kwargs):
        """Dispatch a generic request to the handler for this service's kind.

        Kept intentionally minimal: the registry handler receives ``self``,
        the zeep client and every keyword argument passed here.
        """
        self._ensure_ticket()
        client = self._new_client()
        kind = self.service.value.kind
        handler = get_handler(kind)
        if handler is None:
            raise HandlerNotRegisteredError(
                f"No handler registered for kind '{kind}'. "
                f"Registered kinds: {list_registered_kinds()}."
            )
        return handler(self, client, **kwargs)


# =============================================================================
# Built-in handlers for the padron family.
# =============================================================================


@register_handler("padron_list")
def _padron_list_handler(wsn: WSN, client: zeep.Client, *, persona_ids: list) -> list:
    """Batch call — AFIP returns a list in one request (getPersonaList_v2)."""
    ticket = wsn.authorization_ticket
    persona_ids_long = [int(pid) for pid in persona_ids]
    response = client.service.getPersonaList_v2(
        token=ticket.token,
        sign=ticket.sign,
        cuitRepresentada=int(ticket.number_cuit),
        idPersona=persona_ids_long,
    )
    personas = []
    for i, persona in enumerate(response["persona"]):
        personas.append({persona_ids[i]: zeep.helpers.serialize_object(persona)})
    return personas


@register_handler("padron_single")
def _padron_single_handler(wsn: WSN, client: zeep.Client, *, persona_ids: list) -> list:
    """Per-id call — AFIP only accepts a single id per request (getPersona)."""
    ticket = wsn.authorization_ticket
    personas = []
    for pid in persona_ids:
        try:
            response = client.service.getPersona(
                token=ticket.token,
                sign=ticket.sign,
                cuitRepresentada=int(ticket.number_cuit),
                idPersona=int(pid),
            )
            personas.append({pid: zeep.helpers.serialize_object(response["persona"])})
        except Exception as e:
            personas.append({pid: e})
    return personas
