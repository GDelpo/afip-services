import datetime as dt
import re

from ..logger import get_logger

logger = get_logger(__name__)


class TicketAutorizacion:
    def __init__(self, response_dict: dict):
        logger.info("Initializing TicketAutorizacion with response_dict")
        login_ticket_response = response_dict.get("loginTicketResponse", {})
        credentials = login_ticket_response.get("credentials", {})
        header = login_ticket_response.get("header", {})

        # INTENTIONAL: token and sign are credentials; they are never logged.
        self.token = credentials.get("token")
        self.sign = credentials.get("sign")

        expiration_str = header.get("expirationTime")
        try:
            self.expiration_time = dt.datetime.fromisoformat(expiration_str)
            logger.debug(f"Expiration time parsed successfully: {self.expiration_time}")
        except Exception as e:
            logger.exception(f"Error parsing expirationTime: {expiration_str}")
            raise e

        destination = header.get("destination", "")
        self.number_cuit = self._extract_cuit(destination)
        logger.debug(f"CUIT extracted: {self.number_cuit}")

    def _extract_cuit(self, destination: str) -> str | None:
        logger.debug(f"Extracting CUIT from destination: {destination}")
        match = re.search(r"CUIT (\d+)", destination)
        result = match.group(1) if match else None
        if result:
            logger.debug(f"CUIT found: {result}")
        else:
            logger.warning("CUIT not found in destination")
        return result

    def is_valid(self) -> bool:
        current_time = dt.datetime.now(dt.timezone.utc).astimezone()
        valid = current_time < self.expiration_time
        logger.debug(
            f"Checking ticket validity: now = {current_time}, "
            f"expiration = {self.expiration_time}, is_valid = {valid}"
        )
        return valid

    def __str__(self) -> str:
        # INTENTIONAL: masked, so printing or logging a ticket never leaks token/sign.
        return (
            "Token: ***\n"
            "Sign: ***\n"
            f"Expiration Time: {self.expiration_time}\n"
            f"CUIT: {self.number_cuit}"
        )
