import os

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

from logger import get_logger

logger = get_logger(__name__)


def load_certificate(certificate_path: str):
    logger.debug(f"Iniciando carga del certificado desde: {certificate_path}")
    if not os.path.exists(certificate_path):
        logger.error(f"Archivo de certificado no encontrado: {certificate_path}")
        raise FileNotFoundError(f"Certificate file not found: {certificate_path}")
    with open(certificate_path, "rb") as cert_file:
        certificate = x509.load_pem_x509_certificate(
            cert_file.read(), backend=default_backend()
        )
    logger.info("Certificado cargado correctamente")
    return certificate


def load_private_key(private_key_path: str, passphrase: str | None = None):
    logger.debug(f"Iniciando carga de la clave privada desde: {private_key_path}")
    if not os.path.exists(private_key_path):
        logger.error(f"Archivo de clave privada no encontrado: {private_key_path}")
        raise FileNotFoundError(f"Private key file not found: {private_key_path}")
    with open(private_key_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=passphrase.encode() if passphrase else None,
            backend=default_backend(),
        )
    logger.info("Clave privada cargada correctamente")
    return private_key
