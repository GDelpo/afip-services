import datetime as dt
import re

from logger import get_logger

logger = get_logger(__name__)


class TicketAutorizacion:
    def __init__(self, response_dict: dict):
        logger.info("Inicializando TicketAutorizacion con response_dict")
        login_ticket_response = response_dict.get("loginTicketResponse", {})
        credentials = login_ticket_response.get("credentials", {})
        header = login_ticket_response.get("header", {})

        self.token = credentials.get("token")
        self.sign = credentials.get("sign")
        logger.debug(f"Token obtenido: {self.token}")
        logger.debug(f"Sign obtenido: {self.sign}")

        expiration_str = header.get("expirationTime")
        try:
            self.expiration_time = dt.datetime.fromisoformat(expiration_str)
            logger.debug(
                f"Expiration time parseado correctamente: {
                    self.expiration_time}"
            )
        except Exception as e:
            logger.exception(f"Error al parsear expirationTime: {expiration_str}")
            raise e

        destination = header.get("destination", "")
        self.number_cuit = self._extract_cuit(destination)
        logger.debug(f"CUIT extraído: {self.number_cuit}")

    def _extract_cuit(self, destination: str) -> str | None:
        logger.debug(f"Extrayendo CUIT de destination: {destination}")
        match = re.search(r"CUIT (\d+)", destination)
        result = match.group(1) if match else None
        if result:
            logger.debug(f"CUIT encontrado: {result}")
        else:
            logger.warning("No se encontró CUIT en destination")
        return result

    def is_valid(self) -> bool:
        current_time = dt.datetime.now(dt.timezone.utc).astimezone()
        valid = current_time < self.expiration_time
        logger.debug(
            f"Chequeando validez del ticket: now = {current_time}, expiration = {
                self.expiration_time}, is_valid = {valid}"
        )
        return valid

    def __str__(self) -> str:
        logger.debug("Generando representación string del TicketAutorizacion")
        return (
            f"Token: {self.token}\n"
            f"Sign: {self.sign}\n"
            f"Expiration Time: {self.expiration_time}\n"
            f"CUIT: {self.number_cuit}"
        )
