"""Utilitários HTTP com retry e backoff exponencial."""

import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

import requests

logger = logging.getLogger(__name__)

T = TypeVar("T")


def retry_com_backoff(
    max_tentativas: int = 3,
    backoff_base: float = 1.0,
    backoff_max: float = 30.0,
    excecoes: tuple[type[Exception], ...] = (
        requests.exceptions.Timeout,
        requests.exceptions.ConnectionError,
        requests.exceptions.HTTPError,
    ),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator para retry com backoff exponencial.

    Args:
        max_tentativas: Número máximo de tentativas (padrão: 3).
        backoff_base: Tempo base de espera em segundos (padrão: 1.0).
        backoff_max: Tempo máximo de espera em segundos (padrão: 30.0).
        excecoes: Tupla de exceções que disparam retry.

    Returns:
        Função decorada com retry.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            ultima_excecao: Exception | None = None

            for tentativa in range(1, max_tentativas + 1):
                try:
                    return func(*args, **kwargs)
                except excecoes as exc:
                    ultima_excecao = exc
                    if tentativa == max_tentativas:
                        logger.error(
                            "Todas as %d tentativas falharam para %s: %s",
                            max_tentativas,
                            func.__name__,
                            exc,
                        )
                        raise

                    tempo_espera = min(backoff_base * (2 ** (tentativa - 1)), backoff_max)
                    logger.warning(
                        "Tentativa %d/%d falhou para %s: %s. Aguardando %.1fs antes de retry...",
                        tentativa,
                        max_tentativas,
                        func.__name__,
                        exc,
                        tempo_espera,
                    )
                    time.sleep(tempo_espera)

            raise ultima_excecao  # type: ignore[misc]

        return wrapper

    return decorator


def configurar_logging() -> None:
    """Configura logging estruturado para arquivo e console."""
    import os
    from logging.handlers import RotatingFileHandler

    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, "afiliados.log")

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Handler para arquivo com rotação
    file_handler = RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    # Configura logger raiz
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.handlers.clear()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Reduz verbosidade de bibliotecas terceiras
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
