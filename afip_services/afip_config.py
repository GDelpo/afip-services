from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class ServiceEnvironment:
    service_url: str
    wsdl_url: str


@dataclass(frozen=True)
class ServiceConfig:
    testing: ServiceEnvironment
    production: ServiceEnvironment
    service_name: str  # Nombre usado para crear el TRA XML
    method_name: str  # Método que se invoca en el servicio


class WSNService(Enum):
    WS_SR_CONSTANCIA_INSCRIPCION = ServiceConfig(
        testing=ServiceEnvironment(
            service_url="https://awshomo.afip.gov.ar/sr-padron/webservices/personaServiceA5",
            wsdl_url="https://awshomo.afip.gov.ar/sr-padron/webservices/personaServiceA5?WSDL",
        ),
        production=ServiceEnvironment(
            service_url="https://aws.afip.gov.ar/sr-padron/webservices/personaServiceA5",
            wsdl_url="https://aws.afip.gov.ar/sr-padron/webservices/personaServiceA5?WSDL",
        ),
        service_name="ws_sr_constancia_inscripcion",
        method_name="getPersonaList_v2",
    )
    WS_SR_PADRON_A13 = ServiceConfig(
        testing=ServiceEnvironment(
            service_url="https://awshomo.afip.gov.ar/sr-padron/webservices/personaServiceA13",
            wsdl_url="https://awshomo.afip.gov.ar/sr-padron/webservices/personaServiceA13?WSDL",
        ),
        production=ServiceEnvironment(
            service_url="https://aws.afip.gov.ar/sr-padron/webservices/personaServiceA13",
            wsdl_url="https://aws.afip.gov.ar/sr-padron/webservices/personaServiceA13?WSDL",
        ),
        service_name="ws_sr_padron_a13",
        method_name="getPersona",
    )

    def get_environment(self, is_production: bool):
        return self.value.production if is_production else self.value.testing

    def get_service_name(self):
        return self.value.service_name

    def get_method_name(self):
        return self.value.method_name
