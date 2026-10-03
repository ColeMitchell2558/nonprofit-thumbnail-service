import httpx
import pytest

from nonprofit_thumbnails.infrai_client import InfraiError, InfraiImageClient


@pytest.mark.asyncio
async def test_business_rejection_is_read_from_envelope_before_status() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.headers["Authorization"] == "Bearer test-key"
        assert request.headers["Idempotency-Key"]
        return httpx.Response(
            400,
            json={
                "ok": False,
                "data": None,
                "error": {"code": "INVALID_INPUT", "message": "width is invalid"},
                "metadata": {},
            },
        )

    client = InfraiImageClient("test-key", transport=httpx.MockTransport(handler))
    with pytest.raises(InfraiError) as caught:
        await client.process({"image": "asset", "width": 0})
    await client.close()

    assert caught.value.code == "INVALID_INPUT"
    assert caught.value.status_code == 400


@pytest.mark.asyncio
async def test_rate_limit_honors_retry_after() -> None:
    calls = 0
    delays: list[float] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(
                429,
                headers={"Retry-After": "3"},
                json={"ok": False, "data": None, "error": {}, "metadata": {}},
            )
        return httpx.Response(
            200,
            json={"ok": True, "data": {"id": "thumb_02"}, "error": None, "metadata": {}},
        )

    async def record_sleep(delay: float) -> None:
        delays.append(delay)

    client = InfraiImageClient(
        "test-key",
        transport=httpx.MockTransport(handler),
        sleep=record_sleep,
    )
    result = await client.process({"image": "asset", "width": 640})
    await client.close()

    assert result == {"id": "thumb_02"}
    assert calls == 2
    assert delays == [3.0]
