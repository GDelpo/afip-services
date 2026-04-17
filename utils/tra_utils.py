import datetime as dt

import xmltodict

from logger import get_logger

logger = get_logger(__name__)


def create_tra_xml(service_name: str, delta_minutes: int = 10) -> str:
    logger.info(
        f"Creando XML TRA para el servicio: {service_name} con delta_minutes: {delta_minutes}"
    )
    start_time = dt.datetime.now() - dt.timedelta(minutes=delta_minutes)
    end_time = start_time + dt.timedelta(minutes=2 * delta_minutes)
    logger.debug(f"start_time: {start_time}, end_time: {end_time}")
    tra_data = {
        "loginTicketRequest": {
            "@version": "1.0",
            "header": {
                "uniqueId": start_time.strftime("%y%m%d"),
                "generationTime": start_time.strftime("%Y-%m-%dT%H:%M:%S"),
                "expirationTime": end_time.strftime("%Y-%m-%dT%H:%M:%S"),
            },
            "service": service_name,
        }
    }
    xml_result = xmltodict.unparse(tra_data, pretty=True)
    logger.info("XML TRA creado exitosamente")
    return xml_result
