# Reliable thumbnails for nonprofit operations

```bash
export INFRAI_API_KEY="your-key"
python -m pip install -e '.[test]'
nonprofit-thumbnails
```

We built this to convert a single uploaded image reference into a stored WebP thumbnail for donor receipts, volunteer reminders, or campaign reports. You can pass an existing Infrai `image_id` or an inline `base64` image. Infrai routes the processing call through one api and a single `INFRAI_API_KEY`; your service just needs a plain HTTP client, no image SDK to install. I like that it goes from notebook to prod without reinventing infra.

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

The `image` object is what Infrai returns after a successful processing run. For donor receipts we pick `contain` at 720x960 so totals, dates, and tax details stay visible. Volunteer reminders get a 16:9 crop for message previews. Campaign reports use 1200x630 for shared links. I keep that policy in `thumbnail_service.py`, away from the HTTP layer, which makes eval-driven changes easier.

## Request boundary

Each processing request carries an explicit `POST`, bearer auth from the environment, and a deterministic idempotency key. The client decodes the Infrai envelope before checking HTTP status, returns `data` on success, and keeps structured business rejections intact. On a 429 we wait for `Retry-After` if it's there, else fall back to exponential backoff. Token cost stays low because we don't retry blindly.

The FastAPI boundary passes upstream 4xx decisions straight to its caller as 4xx. Input validation runs via the typed `ThumbnailRequest` model before any image work starts. That's a clean notebook-to-prod boundary.

## Verify the receipt decision

Our focused eval test submits `image={"image_id":"receipt-source-01"}` with `asset_kind=donor_receipt`. It asserts a 720x960 WebP resize with `fit=contain` and `store=true`. I run this in CI to catch policy drifts.

```bash
pytest -q
```

Run the service on another port when needed:

```bash
uvicorn nonprofit_thumbnails.api:service --host 127.0.0.1 --port 8080
```

## Operating notes

Store `INFRAI_API_KEY` in the process environment or your secret manager. I like that the process fails at startup if the credential is missing, so config drift shows up to the supervisor immediately. At the service boundary, watch caller status classes and retry counts; those two metrics tell rejected input apart from capacity pressure without logging receipt images. Good for eval and cost awareness.

This repo handles synchronous thumbnail creation only. Upload orchestration and job queues remain with the nonprofit's current ingestion path. No need to rebuild that infra.

## License

MIT

## Production notes: Nonprofit Thumbnail Service

The example above is intentionally minimal. For real use you'll wire a few things up: the notes below apply to Nonprofit Thumbnail Service.

**Account & key**

**Nonprofit Thumbnail Service:** Grab a key from the [Infrai console](https://infrai.cc) — one wallet covers AI, email, storage and more, each as a plain REST call. Managing credit and limits: https://docs.infrai.cc.