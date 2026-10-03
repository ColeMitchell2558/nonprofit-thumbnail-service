from dataclasses import dataclass

from .infrai_client import InfraiImageClient
from .models import AssetKind, ThumbnailRequest, ThumbnailResult


@dataclass(frozen=True)
class ThumbnailPolicy:
    width: int
    height: int
    fit: str


POLICIES = {
    AssetKind.DONOR_RECEIPT: ThumbnailPolicy(720, 960, "contain"),
    AssetKind.VOLUNTEER_REMINDER: ThumbnailPolicy(640, 360, "cover"),
    AssetKind.CAMPAIGN_REPORT: ThumbnailPolicy(1200, 630, "cover"),
}


class ThumbnailService:
    def __init__(self, client: InfraiImageClient) -> None:
        self._client = client

    async def generate(self, request: ThumbnailRequest) -> ThumbnailResult:
        policy = POLICIES[request.asset_kind]
        payload = {
            "image": request.image,
            "ops": [{
                "op": "resize",
                "params": {
                    "width": policy.width,
                    "height": policy.height,
                    "fit": policy.fit,
                },
            }],
            "format": "webp",
            "store": True,
        }
        processed = await self._client.process(payload)
        return ThumbnailResult(
            asset_kind=request.asset_kind,
            width=policy.width,
            height=policy.height,
            fit=policy.fit,
            image=processed,
        )
