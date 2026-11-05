# afip-services

<p>
  <img alt="Python" src="https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-green">
  <img alt="Version" src="https://img.shields.io/badge/version-0.2.0-blueviolet">
</p>

> Python client for the AFIP/ARCA SOAP web services: WSAA authentication plus the padron / constancia de inscripción queries, extensible through a YAML catalog and a handler registry.

## Features

- WSAA authentication: signs the login ticket request (TRA) with your certificate, gets the ticket and renews it when it expires.
- `dummy` health calls and persona lookups, in batch (`getPersonaList_v2`) or one id per call (`getPersona`).
- **YAML catalog**: adding a padron-family service means editing `services.yaml`.
- **Handler registry**: new service kinds plug in with `@register_handler("my_kind")`.
- Rotating file logs, console output in debug mode and optional Logtail. Token and sign are never logged.

## Requirements

- Python 3.10+
- An AFIP digital certificate and its private key, registered and active for the services you call.
- Network access to the AFIP endpoints (`wsaa.afip.gov.ar` in production, `wsaahomo.afip.gov.ar` in testing).

## Quickstart

### Install

```bash
pip install git+https://github.com/GDelpo/afip-services.git@main
```

With Logtail support: `pip install "afip-services[logtail] @ git+https://github.com/GDelpo/afip-services.git@main"`.

### Use

```python
from afip_services import WSN, WSNService

svc = WSN(
    WSNService.WS_SR_PADRON_A13,
    cert_path="cert.crt",
    key_path="key.key",
    is_production=True,
    passphrase=None,
)
data = svc.request_persona_list(["20111111112"])  # example CUIT
```

`request_persona_list` gets a ticket on the first call and a new one once it expires.

### Result format

One `{id: data}` dict per requested id, in the order you asked for them, keyed by the id exactly as you passed it:

```python
[
    {"20111111112": {"datosGenerales": {"idPersona": 20111111112, ...}}},
    {"20222222223": {"error": "not returned by AFIP"}},
]
```

- `padron_list` services match each answer to its id through `idPersona` (in `datosGenerales`, or in `errorConstancia` when AFIP rejects the id). An id AFIP did not answer gets `{"error": "not returned by AFIP"}`. An answer without `idPersona` raises `AFIPRequestError` instead of being guessed.
- `padron_single` services call AFIP once per id. A failed call becomes `{"error": "<message>"}` and the rest of the batch goes on.

Every value is plain data, so the result can go straight to `json.dumps`.

### Live smoke test

`examples/smoke.py` checks both built-in services against AFIP and looks up the CUITs you pass. It needs a real certificate:

```bash
git clone https://github.com/GDelpo/afip-services.git
cd afip-services
python -m venv env
source env/bin/activate          # Windows: .\env\Scripts\Activate.ps1
pip install -e .
cp .env.example .env             # then set the certificate paths
python examples/smoke.py 20111111112
```

## Configuration

The library reads these from the environment. In a source checkout, a `.env` at the repo root is picked up too.

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_DIR_PATH` | `logs` | Folder for `process.log` and `error.log`, created at import time. |
| `DEBUG` | `False` | `true` turns on DEBUG level and console output. |
| `LOGTAIL_TOKEN` | — | Sends logs to Logtail. Needs the `logtail` extra. |
| `AFIP_SERVICES_CATALOG` | packaged `services.yaml` | Path to a YAML catalog that replaces the default one. |

`examples/smoke.py` also reads the variables below. The library itself takes these values as arguments to `WSN`.

| Variable | Description |
|----------|-------------|
| `CERTIFICATE_PATH` | AFIP certificate (`.crt` / `.pem`). |
| `PRIVATE_KEY_PATH` | Private key matching the certificate. |
| `PASSPHRASE` | Private key passphrase, if any. |
| `IS_PRODUCTION` | `true` (default) for production, `false` for testing (homologación). |

## Extending

### Level 1: add a padron-family service (YAML only)

The padron family (A4, A5, A10, A13, constancia de inscripción) shares one shape: CUITs in, personas out. Add an entry to `afip_services/services.yaml`:

```yaml
services:
  WS_SR_PADRON_A4:
    testing_service_url: https://awshomo.afip.gov.ar/sr-padron/webservices/personaServiceA4
    testing_wsdl_url: https://awshomo.afip.gov.ar/sr-padron/webservices/personaServiceA4?WSDL
    production_service_url: https://aws.afip.gov.ar/sr-padron/webservices/personaServiceA4
    production_wsdl_url: https://aws.afip.gov.ar/sr-padron/webservices/personaServiceA4?WSDL
    service_name: ws_sr_padron_a4
    method_name: getPersona
    kind: padron_single     # or padron_list; check the WSDL
```

`WSNService.WS_SR_PADRON_A4` is generated at import time. To use your own catalog without forking, set `AFIP_SERVICES_CATALOG=/path/to/your.yaml` or call `afip_services.reload_catalog(path)`.

### Level 2: add a non-padron service (custom handler)

Services such as `wsfe` (electronic invoicing), `wsmtx` or `wsfexv1` have other shapes. Declare them with a custom `kind`:

```yaml
services:
  WSFE:
    testing_service_url: https://wswhomo.afip.gov.ar/wsfev1/service.asmx
    testing_wsdl_url: https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL
    production_service_url: https://servicios1.afip.gov.ar/wsfev1/service.asmx
    production_wsdl_url: https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL
    service_name: wsfe
    method_name: FECAESolicitar
    kind: factura_electronica
```

Then register a handler before calling `WSN.request(...)`:

```python
from afip_services import register_handler


@register_handler("factura_electronica")
def wsfe_handler(wsn, client, **kwargs):
    ticket = wsn.authorization_ticket
    return client.service.FECAESolicitar(
        Auth={"Token": ticket.token, "Sign": ticket.sign, "Cuit": int(ticket.number_cuit)},
        FeCAEReq=kwargs["invoice_request"],
    )
```

The package ships the `padron_list` and `padron_single` kinds. Calling a service whose kind has no handler raises `HandlerNotRegisteredError`.

## Tests

```bash
pip install -r requirements-dev.txt -e .
ruff check . && ruff format --check .
pytest
```

The suite runs offline and covers the catalog and registry, the TRA XML, ticket parsing, CMS signing with a self-signed certificate the test generates, and both padron handlers against a fake SOAP client. CI runs it on Python 3.10 and 3.14. None of it talks to AFIP; `examples/smoke.py` does that.

## Architecture

```
afip-services/
├── pyproject.toml                 # packaging (setuptools), ruff and pytest config
├── afip_services/
│   ├── __init__.py                # public API
│   ├── services.yaml              # service catalog (editable)
│   ├── catalog.py                 # YAML loader + dynamic WSNService enum
│   ├── registry.py                # @register_handler for custom kinds
│   ├── afip_gateway.py            # WSN class + built-in padron handlers
│   ├── afip_config.py             # backwards-compatible re-exports
│   ├── logger.py                  # logging setup (Logtail optional)
│   ├── services/wsaa_client.py    # WSAA authentication
│   ├── models/ticket.py           # TicketAutorizacion
│   └── utils/                     # certificate loading, signing, TRA, exceptions
├── examples/smoke.py              # live check against AFIP
└── tests/                         # offline pytest suite
```

**Stack:** `zeep` (SOAP), `cryptography` (CMS signing), `xmltodict`, `pyyaml` (catalog), `python-dotenv`.

## Related

- [`afip-services-api`](https://github.com/GDelpo/afip-services-api): FastAPI service that exposes this client over REST.

## License

[MIT](LICENSE) © 2026 Guido Delponte
