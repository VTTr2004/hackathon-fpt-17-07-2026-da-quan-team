from pathlib import Path


def load_ingestion_prompt() -> str:
    return (Path(__file__).parent / "cash_flow_ingestion.system.md").read_text(encoding="utf-8")


__all__ = ["load_ingestion_prompt"]
