import xmltodict
import zeep

from logger import get_logger

from ..models.ticket import TicketAutorizacion
from ..utils.crypto_utils import load_certificate, load_private_key
from ..utils.exceptions import AFIPAuthenticationError
from ..utils.signing import sign_tra
from ..utils.tra_utils import create_tra_xml

logger = get_logger(__name__)


class WSAAClient:
    def __init__(
        self,
        service_name: str,
        certificate_path: str,
        private_key_path: str,
        is_production: bool = True,
        passphrase: str | None = None,
    ):
        logger.info(f"Inicializando WSAAClient para el servicio: {service_name}")
        self.service_name = service_name
        try:
            self.certificate = load_certificate(certificate_path)
            logger.info("Certificado cargado correctamente")
        except Exception as e:
            logger.exception(
                f"Error al cargar el certificado desde: {certificate_path}"
            )
            raise e
        try:
            self.private_key = load_private_key(private_key_path, passphrase)
            logger.info("Clave privada cargada correctamente")
        except Exception as e:
            logger.exception(
                f"Error al cargar la clave privada desde: {private_key_path}"
            )
            raise e
        self.is_production = is_production
        self.authorization = None

    def request_afip_authorization(self, cms_base64: str) -> dict:
        wsdl_url = self.get_wsdl_url()
        logger.info(f"Solicitando autorización AFIP usando WSDL: {wsdl_url}")
        client = zeep.Client(wsdl=wsdl_url)
        try:
            response = client.service.loginCms(in0=cms_base64)
            logger.info("Respuesta recibida del servicio AFIP")
            return xmltodict.parse(response)
        except Exception as e:
            logger.exception("Error al llamar al servicio AFIP")
            raise AFIPAuthenticationError(f"Error when calling AFIP service: {str(e)}")

    def get_wsdl_url(self) -> str:
        if self.is_production:
            url = "https://wsaa.afip.gov.ar/ws/services/LoginCms?WSDL"
        else:
            url = "https://wsaahomo.afip.gov.ar/ws/services/LoginCms?WSDL"
        logger.debug(f"Utilizando URL de WSDL: {url}")
        return url

    def authenticate(self):
        logger.info("Iniciando proceso de autenticación")
        try:
            tra_xml = create_tra_xml(self.service_name)
            logger.debug("TRA XML creado correctamente")
            signed_cms = sign_tra(tra_xml, self.certificate, self.private_key)
            logger.debug("CMS firmado correctamente")
            self.authorization = self.request_afip_authorization(signed_cms)
            logger.info("Autenticación completada exitosamente")
        except Exception as e:
            logger.exception(
                f"Error durante el proceso de autenticación {
                    str(e)}"
            )
            raise

    def get_authorization_ticket(self):
        if self.authorization is None:
            logger.error("No se pudo obtener el ticket: autorización no disponible")
            raise ValueError("Authorization is not available.")
        logger.info("Ticket de autorización obtenido exitosamente")
        return TicketAutorizacion(self.authorization)
