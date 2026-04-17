import zeep

from logger import get_logger

from .afip_config import WSNService
from .services.wsaa_client import WSAAClient

logger = get_logger(__name__)


class WSN:
    def __init__(
        self,
        service: WSNService,
        cert_path: str,
        key_path: str,
        is_production: bool = True,
        passphrase: str | None = None,
    ):
        """
        Clase que engloba el proceso completo para interactuar con el servicio AFIP.

        Args:
            service (WSNService): Miembro del enum que define la configuración del servicio.
            cert_path (str): Ruta al certificado AFIP.
            key_path (str): Ruta a la clave privada.
            is_production (bool): Indica si se usa el entorno de producción.
            passphrase (str, opcional): Contraseña de la clave privada, si aplica.
        """
        self.service = service  # Ej: WSNService.WS_SR_CONSTANCIA_INSCRIPCION
        # Extraemos la configuración del servicio a partir del enum
        service_config = service.value
        self.wsaa_client = WSAAClient(
            service_config.service_name, cert_path, key_path, is_production, passphrase
        )
        self.authorization_ticket = None

    def obtain_authorization_ticket(self):
        """
        Obtiene el ticket de autorización mediante WSAAClient.
        """
        logger.info("Obteniendo ticket de autorización...")
        self.wsaa_client.authenticate()
        self.authorization_ticket = self.wsaa_client.get_authorization_ticket()

    def request_afip_dummy(self) -> bool:
        """
        Envía una solicitud dummy al servicio AFIP para verificar su operatividad.

        Returns:
            bool: True si el servicio AFIP responde correctamente, False de lo contrario.
        """
        wsdl_url = self.get_wsn_url()
        logger.info(f"Solicitando dummy a AFIP usando WSDL: {wsdl_url}")
        client = zeep.Client(wsdl=wsdl_url)
        try:
            response = client.service.dummy()
            is_operational = (
                response["appserver"] == "OK"
                and response["authserver"] == "OK"
                and response["dbserver"] == "OK"
            )
            return is_operational
        except Exception as e:
            logger.exception("Error en dummy de AFIP")
            raise RuntimeError(f"Error when calling AFIP service: {str(e)}")

    def request_persona_list(self, persona_ids: list) -> list:
        """
        Solicita una lista de personas desde el servicio AFIP.

        Args:
            persona_ids (list): Lista de IDs de personas a recuperar.

        Returns:
            list: Lista de diccionarios con cada ID y su información serializada.
        """
        if not self.authorization_ticket or not self.authorization_ticket.is_valid():
            self.obtain_authorization_ticket()

        wsdl_url = self.get_wsn_url()
        client = zeep.Client(wsdl=wsdl_url)
        method_name = self.service.get_method_name()
        personas_list = []

        try:
            if method_name == "getPersonaList_v2":
                persona_ids_long = [int(pid) for pid in persona_ids]
                response = client.service.getPersonaList_v2(
                    token=self.authorization_ticket.token,
                    sign=self.authorization_ticket.sign,
                    cuitRepresentada=int(self.authorization_ticket.number_cuit),
                    idPersona=persona_ids_long,
                )
                for i, persona in enumerate(response["persona"]):
                    serialized_persona = zeep.helpers.serialize_object(persona)
                    personas_list.append({persona_ids[i]: serialized_persona})
            else:  # Método "getPersona"
                for pid in persona_ids:
                    try:
                        single_response = client.service.getPersona(
                            token=self.authorization_ticket.token,
                            sign=self.authorization_ticket.sign,
                            cuitRepresentada=int(self.authorization_ticket.number_cuit),
                            idPersona=int(pid),
                        )
                        serialized_persona = zeep.helpers.serialize_object(
                            single_response["persona"]
                        )
                        personas_list.append({pid: serialized_persona})
                    except Exception as e:
                        personas_list.append({pid: e})
        except Exception as e:
            logger.exception("Error en request_persona_list")
            raise RuntimeError(f"Error when calling AFIP service: {str(e)}")
        finally:
            return personas_list

    def get_wsn_url(self) -> str:
        """
        Retorna la URL del WSDL para el servicio actual, según el entorno configurado.

        Returns:
            str: La URL del WSDL.
        """
        # Se usa el método get_environment del enum para obtener la
        # configuración del entorno
        env = self.service.get_environment(self.wsaa_client.is_production)
        return env.wsdl_url
