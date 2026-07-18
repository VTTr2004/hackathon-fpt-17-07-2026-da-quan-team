import re
from pathlib import Path

from app.llm.gemini import get_llm_client
from app.services.document_parser import has_extractable_text

OCR_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg"}
_MIME_BY_SUFFIX = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}
_PAGE_HEADING = re.compile(
    r"(?im)^\s*(?:#{1,6}\s*|[-=*]+\s*)?(?:page|trang)\s+(\d+)\s*(?:[-=*]+)?\s*$"
)
_FENCE = re.compile(r"^```(?:text|markdown)?\s*|\s*```$", re.IGNORECASE)


def normalize_ocr_text(raw: str) -> str:
    text = _FENCE.sub("", raw.strip())
    text = _PAGE_HEADING.sub(lambda match: f"[PAGE {match.group(1)}]", text)
    if text and not re.search(r"\[PAGE\s+\d+\]", text, re.IGNORECASE):
        text = f"[PAGE 1]\n{text}"
    return text.strip()


async def ocr_document(path: Path, content_type: str | None = None) -> str:
    suffix = path.suffix.lower()
    if suffix not in OCR_SUFFIXES:
        raise ValueError(f"OCR nhanh chỉ hỗ trợ PDF, PNG và JPEG; nhận {suffix or 'không rõ định dạng'}")
    if not path.is_file():
        raise ValueError("File gốc không còn tồn tại trên hệ thống lưu trữ")
    mime_type = content_type if content_type in set(_MIME_BY_SUFFIX.values()) else _MIME_BY_SUFFIX[suffix]
    text = normalize_ocr_text(
        await get_llm_client().transcribe_document(
            data=path.read_bytes(),
            mime_type=mime_type,
            filename=path.name,
        )
    )
    if not has_extractable_text(text):
        raise ValueError("Gemini OCR không trả về nội dung văn bản")
    return text
