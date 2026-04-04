"""
General-purpose utilities.

Origem:
  retry_on_rate_limit  -> RockItDown/src/helpers/monday_graphql.py:1012-1027
  download_to_local    -> RockItDown/src/helpers/downloader.py
  timestamp_to_datetime -> helpers internos do RockItDown (date_utils)
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, TypeVar

import requests

logger = logging.getLogger(__name__)

T = TypeVar("T")


def retry_on_rate_limit(
    func: Callable[..., T],
    *args: Any,
    max_retries: int = 5,
    retry_delay: float = 5.0,
    rate_limit_marker: str = "ComplexityException",
    **kwargs: Any,
) -> T:
    """
    Executa func(*args, **kwargs) com retry automático em caso de rate limit.

    Origem: RockItDown/src/helpers/monday_graphql.py:retry_on_rate_limit
    Generalizado: aceita marcador de erro configurável.

    Args:
        func: função a chamar
        *args: argumentos posicionais para func
        max_retries: número máximo de tentativas (default: 5)
        retry_delay: segundos entre tentativas (default: 5.0)
        rate_limit_marker: string que identifica erros de rate limit
        **kwargs: argumentos keyword para func

    Raises:
        Exception: o erro original após esgotar as tentativas

    Uso:
        result = retry_on_rate_limit(stripe.Customer.create, name="Acme")
        result = retry_on_rate_limit(
            monday_api_call, board_id=123,
            rate_limit_marker="TooManyRequests",
        )
    """
    last_exc: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            if rate_limit_marker in str(exc):
                last_exc = exc
                if attempt < max_retries:
                    logger.warning(
                        "Rate limit atingido (tentativa %d/%d). Aguardando %.1fs...",
                        attempt, max_retries, retry_delay,
                    )
                    time.sleep(retry_delay)
            else:
                raise
    assert last_exc is not None
    raise last_exc


def download_to_local(url: str, out_path: Path, *, parent_mkdir: bool = True) -> bool:
    """
    Faz download de url para out_path.

    Origem: RockItDown/src/helpers/downloader.py
    Escreve em modo binário para evitar conversões de newline.

    Args:
        url: URL a descarregar
        out_path: caminho de destino (pathlib.Path)
        parent_mkdir: cria directorias pai se não existirem (default: True)

    Returns:
        True em caso de sucesso, False em caso de erro de rede.

    Raises:
        ValueError: se out_path não for um pathlib.Path
    """
    if not isinstance(out_path, Path):
        raise ValueError(f"{out_path!r} deve ser um pathlib.Path")
    if parent_mkdir:
        out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        out_path.write_bytes(resp.content)
        return True
    except requests.RequestException as exc:
        logger.error("Falha ao fazer download de %s: %s", url, exc)
        return False


def timestamp_to_datetime(ts: int | float) -> datetime:
    """
    Converte Unix timestamp (usado pela API Stripe) para datetime UTC com timezone.

    Exemplo:
        dt = timestamp_to_datetime(subscription.current_period_end)
        # datetime(2026, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
    """
    return datetime.fromtimestamp(ts, tz=timezone.utc)
