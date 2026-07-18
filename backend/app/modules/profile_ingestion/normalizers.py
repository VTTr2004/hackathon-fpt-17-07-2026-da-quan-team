import re
import unicodedata
from typing import Any

from .field_registry import FIELD_REGISTRY


def fold_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(character for character in normalized if not unicodedata.combining(character)).casefold()


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def normalize_profile_value(field_key: str, value: Any) -> str | list[str]:
    definition = FIELD_REGISTRY[field_key]
    if definition.value_type == "list":
        if isinstance(value, str):
            raw_items = re.split(r"[,;\n•]+", value)
        elif isinstance(value, list):
            raw_items = [str(item) for item in value]
        else:
            raise ValueError(f"{definition.label} phải là danh sách hoặc chuỗi")
        items = list(dict.fromkeys(_clean_text(item) for item in raw_items if _clean_text(item)))
        if not items:
            raise ValueError(f"{definition.label} không được để trống")
        return items

    if not isinstance(value, str):
        raise ValueError(f"{definition.label} phải là chuỗi")
    cleaned = _clean_text(value)
    if not cleaned:
        raise ValueError(f"{definition.label} không được để trống")
    if len(cleaned) > definition.max_length:
        raise ValueError(f"{definition.label} vượt quá {definition.max_length} ký tự")
    if definition.value_type == "stage":
        folded = fold_text(cleaned).replace("_", " ").replace("-", " ")
        folded = _clean_text(folded)
        aliases = {
            "pre seed": "Pre-seed",
            "preseed": "Pre-seed",
            "seed": "Seed",
            "series a": "Series A",
            "seriesa": "Series A",
            "growth": "Growth",
        }
        if folded not in aliases:
            raise ValueError("Giai đoạn phải là Pre-seed, Seed, Series A hoặc Growth")
        return aliases[folded]
    return cleaned
