"""Download the Vietnam OpenStreetMap extract from Geofabrik.

Usage (from backend/):
    python -m app.modules.surrounding_area.scripts.download_osm

The extract is ~310 MB and is NOT committed to git (see .gitignore). Geofabrik
rebuilds it daily; re-run this monthly and re-run extract_poi.py afterwards so
Evidence.accessed_at stays honest.

Integrity is verified against Geofabrik's published MD5 rather than trusting a
byte count: a truncated or proxy-mangled download that still parses would
silently produce an under-populated map, which is exactly the failure mode this
module exists to prevent (plan section 7.1).
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import time
import urllib.request
from pathlib import Path

PBF_URL = "https://download.geofabrik.de/asia/vietnam-latest.osm.pbf"
MD5_URL = "https://download.geofabrik.de/asia/vietnam-latest.osm.pbf.md5"
DEFAULT_DEST = Path(__file__).resolve().parents[4] / "data" / "vietnam-latest.osm.pbf"

USER_AGENT = "startup-lens-diligence/0.1 (+https://github.com/; OSM extract downloader)"


def _fetch_expected_md5() -> str | None:
    req = urllib.request.Request(MD5_URL, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.read().decode("utf-8").split()[0].strip().lower()
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] cannot fetch published MD5 ({exc}); integrity check skipped", file=sys.stderr)
        return None


def _md5_of(path: Path) -> str:
    digest = hashlib.md5()  # noqa: S324 - matching Geofabrik's published checksum, not security
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().lower()


def download(dest: Path = DEFAULT_DEST, *, force: bool = False) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    expected_md5 = _fetch_expected_md5()

    if dest.exists() and not force:
        if expected_md5 is None:
            print(f"[ok] {dest} already exists; cannot verify without published MD5")
            return dest
        print(f"[..] {dest} exists, verifying MD5")
        if _md5_of(dest) == expected_md5:
            print("[ok] existing file matches published MD5; skipping download")
            return dest
        print("[!!] existing file does NOT match published MD5; re-downloading")

    tmp = dest.with_suffix(dest.suffix + ".part")
    req = urllib.request.Request(PBF_URL, headers={"User-Agent": USER_AGENT})
    started = time.monotonic()
    with urllib.request.urlopen(req, timeout=120) as resp:
        total = int(resp.headers.get("Content-Length", 0))
        last_modified = resp.headers.get("Last-Modified", "unknown")
        print(f"[..] downloading {total / 1e6:.0f} MB (upstream Last-Modified: {last_modified})")
        written = 0
        with tmp.open("wb") as fh:
            while chunk := resp.read(1024 * 1024):
                fh.write(chunk)
                written += len(chunk)
                if total and written % (32 * 1024 * 1024) < 1024 * 1024:
                    print(f"     {written / 1e6:6.0f}/{total / 1e6:.0f} MB")

    if expected_md5 is not None:
        actual = _md5_of(tmp)
        if actual != expected_md5:
            tmp.unlink(missing_ok=True)
            raise RuntimeError(f"MD5 mismatch: expected {expected_md5}, got {actual}. Download discarded.")
        print("[ok] MD5 verified against Geofabrik")

    tmp.replace(dest)
    print(f"[ok] {dest} ({dest.stat().st_size / 1e6:.0f} MB) in {time.monotonic() - started:.0f}s")
    return dest


def main() -> int:
    parser = argparse.ArgumentParser(description="Download the Vietnam OSM extract from Geofabrik")
    parser.add_argument("--dest", type=Path, default=DEFAULT_DEST)
    parser.add_argument("--force", action="store_true", help="re-download even if the file already verifies")
    args = parser.parse_args()
    download(args.dest, force=args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
