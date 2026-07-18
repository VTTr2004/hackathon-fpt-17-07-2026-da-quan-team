import asyncio
import json
import os
from dataclasses import asdict

from app.core.config import get_settings
from app.modules.surrounding_area.providers.geocoding import geocode
from app.modules.surrounding_area.providers.places import lookup_place


async def main() -> None:
    settings = get_settings()
    print(
        json.dumps(
            {
                "google_geocoding_api_key_set": bool(settings.google_geocoding_api_key),
                "google_places_api_key_set": bool(settings.google_places_api_key),
                "goong_api_key_set": bool(settings.goong_api_key),
                "next_public_google_maps_api_key_set": bool(
                    os.getenv("NEXT_PUBLIC_GOOGLE_MAPS_API_KEY")
                ),
            },
            ensure_ascii=False,
        )
    )

    geocode_result = await geocode("Vinhomes Ocean Park, Gia Lam, Ha Noi")
    print(
        json.dumps(
            {
                "geocode_provider": geocode_result.provider,
                "candidates": len(geocode_result.candidates),
                "warnings": geocode_result.warnings,
                "best": asdict(geocode_result.candidates[0])
                if geocode_result.candidates
                else None,
            },
            ensure_ascii=False,
        )
    )

    place_result = lookup_place(
        "Highlands Coffee", 20.993361853000067, 105.95433371300004
    )
    print(
        json.dumps(
            {
                "place_warning": place_result.warning,
                "place": place_result.enrichment.to_dict()
                if place_result.enrichment
                else None,
            },
            ensure_ascii=False,
        )
    )


asyncio.run(main())
