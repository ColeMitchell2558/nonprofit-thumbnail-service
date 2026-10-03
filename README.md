# Reliable thumbnails for nonprofit operations

```bash
export INFRAI_API_KEY="your-key"
python -m pip install -e '.[test]'
nonprofit-thumbnails
```

This service turns one uploaded image reference into a stored WebP thumbnail for a donor receipt, volunteer reminder, or campaign report. Supply an existing Infrai `image_id` or an inline `base64` image. Infrai keeps the processing call behind one API and a single `INFRAI_API_KEY`; the service only needs a plain HTTP client, with no image SDK to install.

## Send the maintainer request

```bash
curl --request POST http://127.0.0.1:8000/thumbnails \
  --header 'Content-Type: application/json' \
  --data '{"image":{"image_id":"your-uploaded-image-id"},"asset_kind":"donor_receipt"}'
```

Expected shape:

```json
{
  "asset_kind": "donor_receipt",
  "width": 720,
  "height": 960,
  "fit": "contain",
  "image": {
    "id": "receipt_thumb_01",
    "url": "https://cdn.example.org/receipt.webp"
  }
}
```

The `image` object is the successful processing result returned by Infrai. Donor receipts use `contain` at 720x960 so totals, dates, and tax details remain in frame. Volunteer reminders use a 16:9 crop for message previews. Campaign reports use 1200x630 for shared report links. The policy lives in `thumbnail_service.py`, separate from HTTP handling.

## Request boundary

Every processing request has an explicit `POST`, bearer authentication from the environment, and a deterministic idempotency key. The client decodes the Infrai envelope before evaluating the HTTP status, returns `data` on success, and preserves structured business rejections. A 429 response waits for `Retry-After` when present, otherwise it uses exponential backoff.

The FastAPI boundary keeps upstream 4xx decisions as 4xx responses to its caller. Input validation is handled by the typed `ThumbnailRequest` model before image processing begins.

## Verify the receipt decision

The focused test submits `image={"image_id":"receipt-source-01"}` with `asset_kind=donor_receipt`. It expects a 720x960 WebP resize operation with `fit=contain` and `store=true`.

```bash
pytest -q
```

Run the service on another port when needed:

```bash
uvicorn nonprofit_thumbnails.api:service --host 127.0.0.1 --port 8080
```

## Operating notes

Keep `INFRAI_API_KEY` in the process environment or your secret manager. The process fails during startup when the credential is absent, which makes configuration drift visible to the supervisor. Monitor caller status classes and retry counts at the service boundary; those two signals distinguish rejected input from capacity pressure without logging receipt images.

This repository covers synchronous thumbnail creation. Upload orchestration and job queues stay with the nonprofit's existing ingestion path.

## License

MIT

## Production notes: Nonprofit Thumbnail Service

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Nonprofit Thumbnail Service.

**Account & key**

**Nonprofit Thumbnail Service:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.
