import xmltodict
import zeep

from ..logger import get_logger
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
        logger.info(f"Initializing WSAAClient for service: {service_name}")
        self.service_name = service_name
        try:
            self.certificate = load_certificate(certificate_path)
            logger.info("Certificate loaded successfully")
        except Exception as e:
            logger.exception(
                f"Error loading certificate from: {certificate_path}"
            )
            raise e
        try:
            self.private_key = load_private_key(private_key_path, passphrase)
            logger.info("Private key loaded successfully")
        except Exception as e:
            logger.exception(
                f"Error loading private key from: {private_key_path}"
            )
            raise e
        self.is_production = is_production
        self.authorization = None

    def request_afip_authorization(self, cms_base64: str) -> dict:
        wsdl_url = self.get_wsdl_url()
        logger.info(f"Requesting AFIP authorization using WSDL: {wsdl_url}")
        client = zeep.Client(wsdl=wsdl_url)
        try:
            response = client.service.loginCms(in0=cms_base64)
            logger.info("Response received from AFIP service")
            return xmltodict.parse(response)
        except Exception as e:
            logger.exception("Error calling AFIP service")
            raise AFIPAuthenticationError(f"Error when calling AFIP service: {str(e)}")

    def get_wsdl_url(self) -> str:
        if self.is_production:
            url = "https://wsaa.afip.gov.ar/ws/services/LoginCms?WSDL"
        else:
            url = "https://wsaahomo.afip.gov.ar/ws/services/LoginCms?WSDL"
        logger.debug(f"Using WSDL URL: {url}")
        return url

    def authenticate(self):
        logger.info("Starting authentication process")
        try:
            tra_xml = create_tra_xml(self.service_name)
            logger.debug("TRA XML created successfully")
            signed_cms = sign_tra(tra_xml, self.certificate, self.private_key)
            logger.debug("CMS signed successfully")
            self.authorization = self.request_afip_authorization(signed_cms)
            logger.info("Authentication completed successfully")
        except Exception as e:
            logger.exception(
                f"Error during authentication process {
                    str(e)}"
            )
            raise

    def get_authorization_ticket(self):
        if self.authorization is None:
            logger.error("Could not obtain ticket: authorization not available")
            raise ValueError("Authorization is not available.")
        logger.info("Authorization ticket obtained successfully")
        return TicketAutorizacion(self.authorization)
