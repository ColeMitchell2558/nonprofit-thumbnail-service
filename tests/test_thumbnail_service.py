import pytest

from nonprofit_thumbnails.models import AssetKind, ThumbnailRequest
from nonprofit_thumbnails.thumbnail_service import ThumbnailService


class RecordingImageClient:
    def __init__(self) -> None:
        self.payload: dict[str, object] | None = None

    async def process(self, payload: dict[str, object]) -> dict[str, str]:
        self.payload = payload
        return {"id": "receipt_thumb_01", "url": "https://cdn.example.org/receipt.webp"}


@pytest.mark.asyncio
async def test_receipt_thumbnail_preserves_the_whole_document() -> None:
    client = RecordingImageClient()
    service = ThumbnailService(client)  # type: ignore[arg-type]

    result = await service.generate(
        ThumbnailRequest(
            image={"image_id": "receipt-source-01"},
            asset_kind=AssetKind.DONOR_RECEIPT,
        )
    )

    assert client.payload == {
        "image": {"image_id": "receipt-source-01"},
        "ops": [{
            "op": "resize",
            "params": {
                "width": 720,
                "height": 960,
                "fit": "contain",
            },
        }],
        "format": "webp",
        "store": True,
    }
    assert result.fit == "contain"
    assert result.image["id"] == "receipt_thumb_01"
