from __future__ import annotations
import json
import re
from typing import Any


def parse_json_array_loose(text: str) -> list[Any]:
    """Try strict JSON parse first. If it fails, try to extract the first top-level JSON array.
    Returns [] on failure.
    """
    text = (text or '').strip()
    if not text:
        return []
    # 1) strict
    try:
        val = json.loads(text)
        return val if isinstance(val, list) else []
    except Exception:
        pass

    # 2) remove code fences
    fence = re.compile(r"^```[a-zA-Z]*\n|\n```$", re.MULTILINE)
    cleaned = fence.sub("\n", text)
    try:
        val = json.loads(cleaned)
        return val if isinstance(val, list) else []
    except Exception:
        pass

    # 3) find first [ ... ] block heuristically
    start = cleaned.find('[')
    end = cleaned.rfind(']')
    if start != -1 and end != -1 and end > start:
        snippet = cleaned[start:end+1]
        try:
            val = json.loads(snippet)
            return val if isinstance(val, list) else []
        except Exception:
            return []
    return []


def parse_json_items_or_array(text: str) -> list[Any]:
    """Parse either a top-level JSON array or an object with 'items' array.
    Returns [] on failure.
    """
    text = (text or '').strip()
    if not text:
        return []
    # try direct array
    arr = parse_json_array_loose(text)
    if isinstance(arr, list) and arr:
        return arr
    # try object with items
    try:
        val = json.loads(text)
        if isinstance(val, dict):
            items = val.get('items') or val.get('data') or val.get('results')
            if isinstance(items, list):
                return items
    except Exception:
        pass
    # try to extract object snippet
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        snippet = text[start:end+1]
        try:
            val = json.loads(snippet)
            if isinstance(val, dict):
                items = val.get('items') or val.get('data') or val.get('results')
                if isinstance(items, list):
                    return items
        except Exception:
            return []
    return []


def salvage_json_items_from_truncated(text: str) -> list[Any]:
    """Best-effort recovery: scan for an array of JSON objects and parse complete ones.
    - Supports either top-level array or object with "items": [ ... ]
    - Ignores the last incomplete object if truncated.
    """
    import json as _json
    s = text or ''
    if not s:
        return []
    # Locate array start
    idx = s.find('"items"')
    if idx != -1:
        arr_start = s.find('[', idx)
    else:
        arr_start = s.find('[')
    if arr_start == -1:
        return []
    i = arr_start + 1
    n = len(s)
    depth = 0
    start = -1
    out: list[Any] = []
    while i < n:
        ch = s[i]
        if ch == '{':
            if depth == 0:
                start = i
            depth += 1
        elif ch == '}':
            if depth > 0:
                depth -= 1
                if depth == 0 and start != -1:
                    frag = s[start:i+1]
                    try:
                        out.append(_json.loads(frag))
                    except Exception:
                        pass
                    start = -1
        elif ch == ']':
            # End of array
            break
        i += 1
    return out
