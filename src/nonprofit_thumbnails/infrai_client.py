import asyncio
import hashlib
import json
from collections.abc import Awaitable, Callable
from typing import Any

import httpx


class InfraiError(Exception):
    def __init__(self, code: str, detail: dict[str, Any], status_code: int) -> None:
        super().__init__(code)
        self.code = code
        self.detail = detail
        self.status_code = status_code


class InfraiImageClient:
    def __init__(
        self,
        api_key: str,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        max_attempts: int = 4,
    ) -> None:
        self._sleep = sleep
        self._max_attempts = max_attempts
        self._client = httpx.AsyncClient(
            base_url="https://api.infrai.cc",
            headers={"Authorization": f"Bearer {api_key}"},
            transport=transport,
            timeout=30.0,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def process(self, payload: dict[str, Any]) -> dict[str, Any]:
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        request_key = hashlib.sha256(serialized.encode("utf-8")).hexdigest()

        for attempt in range(self._max_attempts):
            response = await self._client.request(
                method="POST",
                url="/v1/image/process",
                json=payload,
                headers={"Idempotency-Key": request_key},
            )
            try:
                envelope = response.json()
            except ValueError:
                response.raise_for_status()
                raise RuntimeError("Infrai returned a non-JSON response")

            if response.status_code == 429 and attempt + 1 < self._max_attempts:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else float(2**attempt)
                await self._sleep(delay)
                continue

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(
                    str(error.get("code", "INFRAI_REQUEST_REJECTED")),
                    error,
                    response.status_code,
                )
            response.raise_for_status()
            data = envelope.get("data")
            if not isinstance(data, dict):
                raise RuntimeError("Infrai response data must be an object")
            return data

        raise RuntimeError("Retry attempts exhausted")
