from afip_config import WSNService
from afip_gateway import WSN


def initialize_services(certificate_path, private_key_path, is_production, passphrase):
    wsn_inscription_service = WSN(
        WSNService.WS_SR_CONSTANCIA_INSCRIPCION,
        certificate_path,
        private_key_path,
        is_production,
        passphrase,
    )
    wsn_inscription_service.obtain_authorization_ticket()

    wsn_padron_service = WSN(
        WSNService.WS_SR_PADRON_A13,
        certificate_path,
        private_key_path,
        is_production,
        passphrase,
    )
    wsn_padron_service.obtain_authorization_ticket()

    return wsn_inscription_service, wsn_padron_service


def status_services(wsn_inscription_service, wsn_padron_service) -> str:

    def get_status(service, service_name):
        try:
            return "UP" if service.request_afip_dummy() else "DOWN"
        except Exception as e:
            return f"Error: {e}"

    inscription_status = get_status(wsn_inscription_service, "WSN Inscription Service")
    padron_status = get_status(wsn_padron_service, "WSN Padron Service")

    output = (
        f"WSN Inscription Service: {inscription_status}\n"
        f"WSN Padron Service: {padron_status}"
    )
    return output


if __name__ == "__main__":

    # Variables for init services. Can be set in a config file .env or similar -> Look into logger.py and set settings | You can use the .env-example file
    # from dotenv import load_dotenv
    # import os
    # load_dotenv()
    # os.getenv("CERTIFICATE_PATH")
    certificate_path = "path/to/certificate.crt"
    # os.getenv("PRIVATE_KEY_PATH")
    private_key_path = "path/to/private_key.key"
    is_production = (
        # os.getenv("DEBUG") | False for testing -> NOT WORKING IN TEST MODE
        # AFIP | ARCA PROBLEM
        True
    )
    passphrase = "passphrase"  # os.getenv("PASSPHRASE")

    # Initialize services
    wsn_inscription_service, wsn_padron_service = initialize_services(
        certificate_path, private_key_path, is_production, passphrase
    )

    # Example CUITs LIMITE MAXIMO 250
    cuits = ["NRO CUIT"]

    # Status services
    print(status_services(wsn_inscription_service, wsn_padron_service))

    # Get constancia inscripcion
    list_of_data_retrived = wsn_inscription_service.request_persona_list(cuits)
    print(list_of_data_retrived)

    # Get padron
    list_of_data_retrived = wsn_padron_service.request_persona_list(cuits)
    print(list_of_data_retrived)
