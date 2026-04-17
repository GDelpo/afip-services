import email

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.serialization import pkcs7

from logger import get_logger

logger = get_logger(__name__)


def sign_tra(tra_xml: str, certificate, private_key) -> str:
    logger.info("Iniciando la firma del TRA")
    try:
        cms = (
            pkcs7.PKCS7SignatureBuilder()
            .set_data(tra_xml.encode("utf-8"))
            .add_signer(certificate, private_key, hashes.SHA256())
            .sign(serialization.Encoding.SMIME, [pkcs7.PKCS7Options.Binary])
        )
        logger.debug("Firma CMS generada correctamente")
        msg = email.message_from_string(cms.decode("utf8"))
        for part in msg.walk():
            if part.get_filename() and part.get_filename().startswith("smime.p7"):
                logger.info("Parte CMS encontrada en el mensaje")
                return part.get_payload(decode=False)
        logger.error("No se encontró la parte CMS en el mensaje")
        raise RuntimeError("CMS part not found")
    except Exception as e:
        logger.exception("Error al firmar el TRA")
        raise RuntimeError(f"Error when signing TRA: {str(e)}")
