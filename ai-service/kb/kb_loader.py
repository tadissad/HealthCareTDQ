from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

KB_DIR = Path(__file__).resolve().parent
UNIFIED_KB_PATH = KB_DIR / "unified_kb.json"
KB_CHUNKS_PATH = KB_DIR / "kb_chunks.json"


def load_kb_chunks() -> List[str]:
    if not KB_CHUNKS_PATH.exists():
        return []

    payload = json.loads(KB_CHUNKS_PATH.read_text(encoding="utf-8"))
    chunks: List[str] = []
    for item in payload:
        text = (item.get("text") or "").strip()
        if text:
            chunks.append(text)
    return chunks


def load_kb_metadata() -> Dict:
    if not UNIFIED_KB_PATH.exists():
        return {
            "available": False,
            "path": str(UNIFIED_KB_PATH),
        }

    data = json.loads(UNIFIED_KB_PATH.read_text(encoding="utf-8"))
    return {
        "available": True,
        "path": str(UNIFIED_KB_PATH),
        "generated_at": data.get("metadata", {}).get("generated_at"),
        "sources": data.get("metadata", {}).get("sources", []),
        "products_total": len(data.get("products", [])),
        "categories_total": len(data.get("categories", [])),
        "diseases_total": len(data.get("diseases", [])),
        "symptoms_total": len(data.get("symptoms", [])),
        "chunks_total": len(data.get("chunks", [])),
    }
