"""One-command data setup for the surrounding-area module.

    python -m app.modules.surrounding_area.scripts.setup_data

Downloads the Vietnam OSM extract (~310 MB, verified against Geofabrik's MD5) and
builds `data/poi.db` (~44 MB). Idempotent: if `poi.db` already exists it does
nothing unless `--force`. A teammate who just pulled the repo runs this once and
the module is ready; the extract and db are gitignored so nothing large is
committed.

The app itself does NOT need this to import or to run its tests — a missing
poi.db degrades cleanly to INSUFFICIENT_DATA. This only enables real analysis.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from app.modules.surrounding_area.scripts.download_osm import DEFAULT_DEST, download
from app.modules.surrounding_area.scripts.extract_poi import DEFAULT_DB, extract


def main() -> int:
    parser = argparse.ArgumentParser(description="Download OSM extract + build poi.db in one step")
    parser.add_argument("--force", action="store_true", help="rebuild even if poi.db already exists")
    args = parser.parse_args()

    db_path: Path = DEFAULT_DB
    if db_path.exists() and not args.force:
        print(f"[ok] {db_path} đã tồn tại ({db_path.stat().st_size / 1e6:.0f} MB). "
              f"Dùng --force để build lại. Module đã sẵn sàng.")
        return 0

    print("[1/2] Tải bản trích OpenStreetMap Việt Nam từ Geofabrik...")
    pbf = download(DEFAULT_DEST, force=args.force)

    print("[2/2] Trích xuất POI -> poi.db (có thể mất vài chục giây)...")
    extract(pbf, db_path)

    print("\n[done] poi.db đã sẵn sàng. Chạy: uvicorn app.main:app --reload")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
