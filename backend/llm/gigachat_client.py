import os
import time

import httpx
from gigachat import GigaChat

NETWORK_RETRIES = 5
RETRY_BACKOFF_SEC = 2.0


def _model_name() -> str:
    return os.getenv("GIGACHAT_MODEL", "GigaChat")


def get_client() -> GigaChat:
    api_key = os.getenv("GIGACHAT_API_KEY")
    if not api_key:
        raise RuntimeError("GIGACHAT_API_KEY is not set")
    return GigaChat(
        credentials=api_key,
        scope=os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS"),
        model=_model_name(),
        verify_ssl_certs=os.getenv("GIGACHAT_VERIFY_SSL", "false").lower() == "true",
        timeout=int(os.getenv("GIGACHAT_TIMEOUT", "60")),
    )


def chat(prompt: str, system: str | None = None, temperature: float | None = None) -> str:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    payload: dict = {"messages": messages}
    if temperature is not None:
        payload["temperature"] = temperature

    last_exc: Exception | None = None
    for attempt in range(1, NETWORK_RETRIES + 1):
        try:
            with get_client() as client:
                resp = client.chat(payload)
                return resp.choices[0].message.content
        except httpx.TransportError as e:
            last_exc = e
            if attempt < NETWORK_RETRIES:
                time.sleep(RETRY_BACKOFF_SEC * attempt)
    raise RuntimeError(f"GigaChat network failure after {NETWORK_RETRIES} retries: {last_exc}")
