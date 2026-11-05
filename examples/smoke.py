"""Live smoke test against AFIP: service status plus a lookup of the CUITs given as arguments.

Needs a real AFIP certificate. Reads the same variables as .env.example:
CERTIFICATE_PATH, PRIVATE_KEY_PATH, PASSPHRASE (optional) and IS_PRODUCTION.

    python examples/smoke.py 20111111112 [more CUITs...]
"""

import os
import sys

from dotenv import load_dotenv

from afip_services import WSN, WSNService

MAX_IDS = 250  # AFIP limit per getPersonaList_v2 call


def build(service: WSNService) -> WSN:
    return WSN(
        service,
        os.environ["CERTIFICATE_PATH"],
        os.environ["PRIVATE_KEY_PATH"],
        os.getenv("IS_PRODUCTION", "true").lower() in ("true", "1", "yes"),
        os.getenv("PASSPHRASE") or None,
    )


def main(cuits: list[str]) -> None:
    if not 1 <= len(cuits) <= MAX_IDS:
        sys.exit(f"usage: python examples/smoke.py CUIT [CUIT ...]  (1 to {MAX_IDS} CUITs)")
    for service in (WSNService.WS_SR_CONSTANCIA_INSCRIPCION, WSNService.WS_SR_PADRON_A13):
        wsn = build(service)
        try:
            status = "UP" if wsn.request_afip_dummy() else "DOWN"
        except RuntimeError as exc:
            status = f"error: {exc}"
        print(f"{service.name}: {status}")
        print(wsn.request_persona_list(cuits))


if __name__ == "__main__":
    load_dotenv()
    main(sys.argv[1:])
