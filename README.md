# afip-services

<p>
  <img alt="Python" src="https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-green">
  <img alt="Status" src="https://img.shields.io/badge/status-stable-green">
  <img alt="Version" src="https://img.shields.io/badge/version-0.2.0-blueviolet">
</p>

> Cliente Python para los web services SOAP de AFIP/ARCA: autenticación WSAA + llamadas a la familia `padron`/`inscripción`. **Extensible** vía catálogo YAML y registry de handlers para nuevos servicios (wsfe, wsmtx, wsfexv1, …).

## Features

- Autenticación WSAA: obtención, cache y renovación de tickets.
- Llamadas SOAP `dummy` y consultas de personas (list batch o single-by-id).
- **YAML catalog** — agregar un servicio padron-family = editar `services.yaml`.
- **Handler registry** — nuevos *kinds* de servicio se inscriben con `@register_handler("mi_kind")`. Hook vacío listo para cuando quieras implementar wsfe u otros.
- Manejo de certificado digital + firma XML (`cryptography` + `zeep`).
- Logging con rotating file handlers + Logtail opcional.
- Diseño modular: `afip_gateway.py` orquesta, `catalog.py` lee el YAML, `registry.py` es el extension point, `services/wsaa_client.py` autentica.

## Requirements

- Python 3.10+
- **Certificado digital y clave privada AFIP** registrados y activos.
- Acceso de red a los endpoints AFIP (`wsaa.afip.gov.ar` para prod, homologación para testing).

## Quickstart

### Install as package (recommended)

```bash
pip install git+https://github.com/GDelpo/afip-services.git@main
```

```python
from afip_services import WSN, WSNService

svc = WSN(
    WSNService.WS_SR_PADRON_A13,
    cert_path="cert.crt",
    key_path="key.key",
    is_production=True,
)
svc.obtain_authorization_ticket()
data = svc.request_persona_list(["20300000003"])
```

With Logtail support: `pip install "afip-services[logtail] @ git+https://github.com/GDelpo/afip-services.git@main"`.

### Install from source (development)

```bash
git clone https://github.com/GDelpo/afip-services.git
cd afip-services
python -m venv env
source env/bin/activate          # Linux/macOS
# .\env\Scripts\Activate.ps1     # Windows
pip install -e .
```

### Configure

```bash
cp .env.example .env
# Editar .env con tu cert, key y entorno
python test.py   # smoke test contra AFIP
```

## Extending — two levels of effort

### Level 1 · Add a padron-family service (YAML only)

The padron family (A4 / A5 / A10 / A13 / constancia de inscripción) share the same request/response shape: *CUITs in → personas out*. Adding one = editing `afip_services/services.yaml`:

```yaml
services:
  WS_SR_PADRON_A4:
    testing_service_url: https://awshomo.afip.gov.ar/sr-padron/webservices/personaServiceA4
    testing_wsdl_url: https://awshomo.afip.gov.ar/sr-padron/webservices/personaServiceA4?WSDL
    production_service_url: https://aws.afip.gov.ar/sr-padron/webservices/personaServiceA4
    production_wsdl_url: https://aws.afip.gov.ar/sr-padron/webservices/personaServiceA4?WSDL
    service_name: ws_sr_padron_a4
    method_name: getPersona
    kind: padron_single     # or padron_list — see the WSDL
```

No Python code needed — `WSNService.WS_SR_PADRON_A4` is auto-generated at import time.

Override the default catalog without forking: set `AFIP_SERVICES_CATALOG=/path/to/your.yaml` or call `afip_services.reload_catalog(path)` at runtime.

### Level 2 · Add a non-padron service (custom handler)

Services like `wsfe` (facturación electrónica), `wsmtx`, `wsfexv1` have different shapes. Declare them with a custom `kind`:

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

Then register a handler anywhere in your code before calling `WSN.request(…)`:

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

The built-in kinds shipped with the package are `padron_list` and `padron_single`. Everything else requires a handler — the package raises `HandlerNotRegisteredError` with a clear message if a call is made without one registered.

## Configuration (.env)

| Variable | Descripción |
|----------|-------------|
| `AFIP_CERT_PATH` | Path al certificado `.crt`/`.pem` |
| `AFIP_KEY_PATH` | Path a la clave privada |
| `AFIP_SERVICE_NAME` | Servicio AFIP a autenticar (ej. `ws_sr_padron_a5`) |
| `LOG_DIR_PATH` | Directorio de logs (default `logs/`) |
| `DEBUG` | `true` activa logging DEBUG + consola |
| `LOGTAIL_TOKEN` | Opcional |
| `AFIP_SERVICES_CATALOG` | Opcional — path a un YAML custom que reemplaza el default |

## Architecture

```
afip-services/
├── pyproject.toml                 # Empaquetado pip (setuptools)
├── afip_services/                 # Paquete Python instalable
│   ├── __init__.py                # Re-exporta el API público
│   ├── services.yaml              # ← catálogo de servicios (editable)
│   ├── catalog.py                 # Loader + Enum dinámico
│   ├── registry.py                # Hook para kinds custom (@register_handler)
│   ├── afip_gateway.py            # Clase WSN + built-in padron handlers
│   ├── afip_config.py             # Re-export compat con versiones previas
│   ├── logger.py                  # Logging centralizado (logtail opcional)
│   ├── services/wsaa_client.py    # Autenticación WSAA
│   ├── models/ticket.py           # TicketAutorizacion
│   └── utils/                     # crypto, signing, TRA, exceptions
└── test.py                        # Demo / smoke test
```

**Stack:** `zeep` (SOAP), `cryptography` (firma digital), `pyyaml` (catalog), `python-dotenv` (config).

## Related

- [`afip-services-api`](https://github.com/GDelpo/afip-services-api) — FastAPI REST que expone este cliente con JWT + rate limiting.
- [`afip-services-applied`](https://github.com/GDelpo/afip-services-applied) — ejemplo de consumer que llama a la API.
- [`afip-iva-checker`](https://github.com/GDelpo/afip-iva-checker) — app que procesa libros IVA usando estos servicios.

## License

[MIT](LICENSE) © 2026 Guido Delponte
