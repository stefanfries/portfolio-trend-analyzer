"""
Fetch warrant detail data for all WKNs in megatrend_folger and save to JSON.

The API is hosted on Azure Container Apps (scales to zero), so the first
request may take 30-40 seconds to wake up the instance.

Usage:
    uv run python scripts/fetch_warrant_data.py
"""

import json
import sys
import time
from pathlib import Path

import httpx

# Make app/ importable when running from the repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.depots import megatrend_folger  # noqa: E402

BASE_URL = "https://ca-fastapi.yellowwater-786ec0d0.germanywestcentral.azurecontainerapps.io"
OUTPUT_FILE = Path(__file__).resolve().parents[1] / "results" / "warrant_data.json"

WARMUP_TIMEOUT = 90.0  # first request may need to wake the container (scales to zero)
REQUEST_TIMEOUT = 30.0  # subsequent requests


def fetch_warrant(wkn: str, timeout: float, client: httpx.Client) -> dict:
    url = f"{BASE_URL}/v1/warrants/{wkn}"
    response = client.get(url, timeout=timeout)
    response.raise_for_status()
    return response.json()


def main() -> None:
    results: dict[str, dict] = {}
    errors: dict[str, str] = {}

    total = len(megatrend_folger)
    print(f"Fetching warrant data for {total} WKNs from megatrend_folger...")

    with httpx.Client() as client:
        for i, wkn in enumerate(megatrend_folger):
            timeout = WARMUP_TIMEOUT if i == 0 else REQUEST_TIMEOUT
            label = f"[{i + 1}/{total}]"

            if i == 0:
                print(
                    f"{label} {wkn}  (cold start — waiting up to {int(timeout)}s)...",
                    end=" ",
                    flush=True,
                )
            else:
                print(f"{label} {wkn}...", end=" ", flush=True)

            t0 = time.monotonic()
            try:
                data = fetch_warrant(wkn, timeout=timeout, client=client)
                elapsed = time.monotonic() - t0
                print(f"OK ({elapsed:.1f}s)")
                results[wkn] = data
            except httpx.HTTPStatusError as exc:
                elapsed = time.monotonic() - t0
                msg = f"HTTP {exc.response.status_code}"
                print(f"FAILED — {msg} ({elapsed:.1f}s)")
                errors[wkn] = f"{msg}: {exc.response.text[:300]}"
            except Exception as exc:
                elapsed = time.monotonic() - t0
                print(f"FAILED — {exc} ({elapsed:.1f}s)")
                errors[wkn] = str(exc)

    output = {
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "count": len(results),
        "errors": errors,
        "data": results,
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nSaved {len(results)}/{total} records to {OUTPUT_FILE}")
    if errors:
        print(f"Errors ({len(errors)}): {', '.join(errors.keys())}")


if __name__ == "__main__":
    main()
