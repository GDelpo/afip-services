import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Dict, Optional

from dotenv import load_dotenv
from logtail import LogtailHandler

load_dotenv()

# Config for logger -> You can move to another .py file and import it like
# settings.py
settings = {
    "log_dir_path": os.getenv("LOG_DIR_PATH", "logs"),
    "debug": os.getenv("DEBUG", "False").lower() in ["true", "1", "yes"],
    "logtail_token": os.getenv("LOGTAIL_TOKEN", "your-logtail-token"),
}


class LoggerConfig:
    _instance: Optional["LoggerConfig"] = None
    _loggers: Dict[str, logging.Logger] = {}

    def __new__(cls) -> "LoggerConfig":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._configure()
        return cls._instance

    def _configure(self) -> None:
        # Crear directorio de logs si no existe
        log_dir = Path(settings.log_dir_path)
        log_dir.mkdir(parents=True, exist_ok=True)

        # Configurar el formateador común
        formatter = self._get_formatter()

        # Configurar el logger raíz
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)

        # Agregar handlers
        self._add_file_handlers(root_logger, log_dir, formatter)
        if settings.debug:
            self._add_console_handler(root_logger, formatter)
        if settings.logtail_token:
            self._add_logtail_handler(root_logger, formatter)

    def _get_formatter(self) -> logging.Formatter:
        return logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    def _add_file_handlers(
        self, root_logger: logging.Logger, log_dir: Path, formatter: logging.Formatter
    ) -> None:
        # Handler para logs de proceso
        process_handler = RotatingFileHandler(
            filename=log_dir / "process.log",
            maxBytes=10_000_000,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        process_handler.setFormatter(formatter)
        process_handler.setLevel(logging.DEBUG if settings.debug else logging.INFO)
        process_handler.addFilter(lambda record: record.levelno < logging.ERROR)
        root_logger.addHandler(process_handler)

        # Handler para logs de error
        error_handler = RotatingFileHandler(
            filename=log_dir / "error.log",
            maxBytes=10_000_000,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        error_handler.setFormatter(formatter)
        error_handler.setLevel(logging.ERROR)
        root_logger.addHandler(error_handler)

    def _add_console_handler(
        self, root_logger: logging.Logger, formatter: logging.Formatter
    ) -> None:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(console_handler)

    def _add_logtail_handler(
        self, root_logger: logging.Logger, formatter: logging.Formatter
    ) -> None:
        try:
            logtail_handler = LogtailHandler(source_token=settings.logtail_token)
            logtail_handler.setFormatter(formatter)
            logtail_handler.setLevel(logging.DEBUG if settings.debug else logging.INFO)
            root_logger.addHandler(logtail_handler)
        except Exception as e:
            root_logger.error(f"Error al inicializar LogtailHandler: {e}")

    def get_logger(self, name: str) -> logging.Logger:
        """Obtener una instancia de logger por nombre."""
        if name not in self._loggers:
            logger = logging.getLogger(name)
            # Agregar información contextual
            logger = logging.LoggerAdapter(
                logger,
                {"timestamp": datetime.now().isoformat(), "process_id": os.getpid()},
            )
            self._loggers[name] = logger
        return self._loggers[name]


# Instancia singleton
logger_config = LoggerConfig()


def get_logger(name: str) -> logging.Logger:
    """Función de conveniencia para obtener una instancia de logger."""
    return logger_config.get_logger(name)
