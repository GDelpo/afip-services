# Python AFIP | ARCA Services

## Repositorio

```bash
git clone http://192.168.190.95/forgejo/noble/afip-services.git
git pull origin main   # actualizar
```

> Primera vez en una máquina nueva: ver [SETUP.md](http://192.168.190.95/forgejo/noble/workspace/raw/branch/main/SETUP.md) para configurar proxy y credenciales Git.

---


Este proyecto provee una función para conectarse al servicio de AFIP/ARCA, permitiendo la autenticación mediante WSAA y la realización de solicitudes SOAP para obtener datos (como la lista de personas) de los servicios de AFIP.

## Características

- **Autenticación AFIP:** Se conecta al servicio de WSAA para obtener el ticket de autorización.
- **Consultas SOAP:** Permite realizar llamadas dummy y obtener información de personas desde dos endpoints distintos.
- **Logging Avanzado:** Implementa un sistema de logging con:
  - Rotating File Handlers (archivos separados para logs de proceso y errores).
  - Consola (en modo debug).
  - Integración con Logtail (si se provee un token).
- **Configuración Modular:** Utiliza variables de entorno para gestionar configuraciones sensibles y de ambiente (desarrollo, testing, producción).
- **Código Moderno:** Utiliza características de Python como _dataclasses_, anotaciones de tipo y manejo de excepciones.

## Requisitos Previos

Es **fundamental** contar con un certificado digital y una clave privada válidos, los cuales deben ser suministrados y registrados previamente en AFIP/ARCA para que el proceso de autenticación funcione correctamente.

## Estructura del Proyecto

```bash
|-- __init__.py
|-- .gitignore
|-- README.md
|-- afip_config.py
|-- afip_gateway.py
|-- logger.py
|-- test.py
|-- models
|   |-- __init__.py
|   |-- ticket.py
|-- services
|   |-- __init__.py
|   |-- wsaa_client.py
|-- utils
|   |-- __init__.py
|   |-- crypto_utils.py
|   |-- exceptions.py
|   |-- signing.py
|   |-- tra_utils.py
```

- **afip_config.py:** Define las configuraciones de los servicios y entornos (testing y producción).
- **afip_gateway.py:** Maneja la conexión y solicitud a los servicios de AFIP, utilizando WSAA y realizando llamadas SOAP.
- **logger.py:** Configura el sistema de logging centralizado para toda la aplicación.
- **test.py:** Script de ejemplo para inicializar servicios, obtener tickets y realizar consultas dummy.
- **models:** Define modelos de datos (por ejemplo, el ticket de autorización).
- **services:** Implementa la lógica de autenticación (WSAA).
- **utils:** Contiene funciones auxiliares para manejo de certificados, firma digital, creación de XML y manejo de excepciones.

## Instalación

1. **Clona el repositorio:**

   ```bash
   git clone https://github.com/tu_usuario/python_afip_services.git
   cd python_afip_services
   ```

2. **Crea un entorno virtual (opcional pero recomendado):**

   ```bash
   python -m venv venv
   # En Unix/macOS
   source venv/bin/activate
   # En Windows
   venv\Scripts\activate
   ```

3. **Instala las dependencias:**

   ```bash
   pip install -r requirements.txt
   ```

## Configuración

El proyecto utiliza variables de entorno para la configuración. Se incluye un archivo de ejemplo llamado **.env-example**. Renómbralo a **.env** y ajusta los valores según tus necesidades.

### Ejemplo de archivo `.env`

```env
# Debug mode: True for development, False for production
DEBUG=True

# Directory to store log files
LOG_DIR_PATH=logs

# Token for Logtail (if used, otherwise leave blank)
LOGTAIL_TOKEN=your-logtail-token

# Path to the AFIP certificate (must be valid and registered in AFIP/ARCA)
CERTIFICATE_PATH=path/to/certificate.crt

# Path to the AFIP private key (must be valid and registered in AFIP/ARCA)
PRIVATE_KEY_PATH=path/to/private_key.key

# Indicates whether to use the production environment (True) or testing (False)
IS_PRODUCTION=True

# Passphrase for the private key (if applicable)
PASSPHRASE=your-passphrase
```

### Carga de las Variables de Entorno

Se recomienda utilizar la librería [python-dotenv](https://pypi.org/project/python-dotenv/) para cargar las variables de entorno. Puedes crear un archivo `config.py` de ejemplo:

```python
# config.py
import os
from dotenv import load_dotenv

load_dotenv()  # Carga las variables desde el archivo .env

# Configuración general
DEBUG = os.getenv("DEBUG", "False").lower() in ["true", "1", "yes"]
LOG_DIR_PATH = os.getenv("LOG_DIR_PATH", "logs")
LOGTAIL_TOKEN = os.getenv("LOGTAIL_TOKEN", "")

# Configuración de AFIP
CERTIFICATE_PATH = os.getenv("CERTIFICATE_PATH", "path/to/certificate.crt")
PRIVATE_KEY_PATH = os.getenv("PRIVATE_KEY_PATH", "path/to/private_key.key")
IS_PRODUCTION = os.getenv("IS_PRODUCTION", "False").lower() in ["true", "1", "yes"]
PASSPHRASE = os.getenv("PASSPHRASE", None)
```

Luego, en tus módulos (por ejemplo, en `test.py` o `logger.py`), puedes importar estas variables:

```python
from config import CERTIFICATE_PATH, PRIVATE_KEY_PATH, IS_PRODUCTION, PASSPHRASE
```

## Uso

El archivo principal de ejemplo es **test.py**, el cual demuestra cómo:

- Inicializar los servicios de inscripción y padrón.
- Obtener el ticket de autorización.
- Realizar una solicitud dummy a AFIP.
- Solicitar la lista de personas.

Para ejecutarlo, simplemente corre:

```bash
python test.py
```

Al ejecutarse, se mostrarán en consola los estados de los servicios y se imprimirán los datos recuperados.

## Logging

La configuración del logging se encuentra en **logger.py**. Se utiliza un enfoque centralizado que permite:
- Guardar logs de proceso en `logs/process.log`.
- Guardar errores en `logs/error.log`.
- Mostrar logs en consola cuando se encuentra en modo debug.
- Integrar con Logtail si se proporciona el token correspondiente.

## Contribuciones

Las contribuciones son bienvenidas. Si deseas mejorar alguna funcionalidad o corregir errores, por favor abre un _issue_ o envía un _pull request_.

## Contacto

Para consultas o sugerencias, puedes contactarme a través de [delponte.guidon@gmail.com].
