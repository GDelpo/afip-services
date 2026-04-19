# afip-services

<p>
  <img alt="Python" src="https://img.shields.io/badge/python-3.9%2B-blue?logo=python&logoColor=white">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-green">
  <img alt="Status" src="https://img.shields.io/badge/status-stable-green">
</p>

> Cliente Python base para los web services SOAP de AFIP/ARCA: autenticación WSAA + llamadas a endpoints de padrón e inscripción.

## Features

- Autenticación WSAA contra AFIP: obtención y cache de tickets de autorización.
- Llamadas SOAP dummy y consultas de personas a dos endpoints (`inscription`, `padron`).
- Manejo de certificado digital + firma XML (`cryptography` + `zeep`).
- Logging con rotating file handlers (proceso + errores separados), opcional Logtail.
- Configuración 100% por `.env`: entornos dev/test/prod, paths de cert/key, service name.
- Diseño modular: `afip_gateway.py` orquesta, `services/wsaa_client.py` autentica, `models/` define tickets, `utils/` firma y XML.

## Requirements

- Python 3.9+
- **Certificado digital y clave privada AFIP** registrados y activos — sin esto no hay autenticación posible.
- Acceso de red al endpoint AFIP (`wsaa.afip.gov.ar` para prod, homologación para testing).

## Quickstart

### Install

```bash
git clone https://github.com/GDelpo/afip-services.git
cd afip-services
python -m venv env
source env/bin/activate          # Linux/macOS
# .\env\Scripts\Activate.ps1     # Windows
pip install -r requirements.txt
```

### Configure

```bash
cp .env.example .env
# Editar .env con tu cert, key y entorno
```

### Run demo

```bash
python test.py
```

## Configuration

| Variable | Descripción |
|----------|-------------|
| `AFIP_ENV` | `testing` o `production` |
| `AFIP_CERT_PATH` | Path al certificado `.crt`/`.pem` |
| `AFIP_KEY_PATH` | Path a la clave privada |
| `AFIP_SERVICE_NAME` | Servicio AFIP a autenticar (ej. `ws_sr_padron_a5`) |
| `LOGTAIL_TOKEN` | Token de Logtail (opcional) |

## Architecture

```
afip-services/
├── afip_gateway.py   # Orquestador principal
├── afip_config.py    # Settings por entorno
├── logger.py         # Logging centralizado
├── test.py           # Demo / smoke test
├── services/
│   └── wsaa_client.py   # Autenticación WSAA
├── models/
│   └── ticket.py        # TicketAutorizacion
└── utils/
    ├── crypto_utils.py  # Load cert + key
    ├── signing.py       # Firma XML
    ├── tra_utils.py     # Construye el TRA
    └── exceptions.py    # AFIPAuthenticationError, etc.
```

**Stack:** `zeep` para SOAP, `cryptography` para firma digital, `python-dotenv` para config.

## Relacionados

- [`afip-services-api`](https://github.com/GDelpo/afip-services-api) — FastAPI REST que expone este cliente con JWT + rate limiting.
- [`afip-services-applied`](https://github.com/GDelpo/afip-services-applied) — ejemplo de consumer que llama a la API.
- [`afip-iva-checker`](https://github.com/GDelpo/afip-iva-checker) — app que procesa libros IVA usando estos servicios.

## License

[MIT](LICENSE) © 2026 Guido Delponte
