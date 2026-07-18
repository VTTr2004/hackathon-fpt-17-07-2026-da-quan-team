import json
import os
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_env() -> dict[str, str]:
    values: dict[str, str] = {}
    env_path = ROOT / ".env"
    if not env_path.exists():
        return values
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def key_meta(value: str | None) -> dict[str, object]:
    if not value:
        return {"set": False}
    return {"set": True, "length": len(value), "suffix": value[-4:]}


def fetch_json(url: str, headers: dict[str, str] | None = None) -> dict[str, object]:
    request = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
            return {
                "http": response.status,
                "status": data.get("status"),
                "error_message": data.get("error_message"),
            }
    except Exception as exc:
        return {"error": str(exc)}


def fetch_text_probe(url: str, headers: dict[str, str] | None = None) -> dict[str, object]:
    request = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            text = response.read(4096).decode("utf-8", errors="replace")
            markers = [
                "BillingNotEnabledMapError",
                "InvalidKeyMapError",
                "ApiNotActivatedMapError",
                "RefererNotAllowedMapError",
                "Google Maps JavaScript API error",
            ]
            return {
                "http": response.status,
                "error_markers": [marker for marker in markers if marker in text],
            }
    except Exception as exc:
        return {"error": str(exc)}


env = load_env()
backend_key = env.get("GOOGLE_GEOCODING_API_KEY") or os.getenv("GOOGLE_GEOCODING_API_KEY")
places_key = env.get("GOOGLE_PLACES_API_KEY") or os.getenv("GOOGLE_PLACES_API_KEY")
frontend_key = env.get("NEXT_PUBLIC_GOOGLE_MAPS_API_KEY") or os.getenv(
    "NEXT_PUBLIC_GOOGLE_MAPS_API_KEY"
)

geocode_url = "https://maps.googleapis.com/maps/api/geocode/json?" + urllib.parse.urlencode(
    {"address": "Vinhomes Ocean Park Gia Lam Ha Noi", "key": backend_key or ""}
)
places_url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json?" + urllib.parse.urlencode(
    {
        "input": "Highlands Coffee",
        "inputtype": "textquery",
        "fields": "place_id,name,rating,user_ratings_total,price_level",
        "locationbias": "point:20.993361853000067,105.95433371300004",
        "key": places_key or "",
    }
)
maps_js_url = "https://maps.googleapis.com/maps/api/js?" + urllib.parse.urlencode(
    {"key": frontend_key or "", "callback": "initMap"}
)

print(
    json.dumps(
        {
            "keys": {
                "backend_geocoding": key_meta(backend_key),
                "backend_places": key_meta(places_key),
                "frontend_maps_js": key_meta(frontend_key),
            },
            "google_geocoding": fetch_json(geocode_url),
            "google_places": fetch_json(places_url),
            "google_maps_js": fetch_text_probe(
                maps_js_url,
                headers={"Referer": "http://localhost:3000/"},
            ),
        },
        ensure_ascii=False,
    )
)
