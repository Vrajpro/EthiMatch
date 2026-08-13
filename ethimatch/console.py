"""Safe console output and JSON serialization helpers."""

from __future__ import annotations

import json
import sys
from typing import Any

def _configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if stream is not None and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass

_configure_stdio()

def safe_print(*args, **kwargs) -> None:
    """Print text without crashing on Windows charmap encodings."""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        end = kwargs.get("end", "\n")
        sep = kwargs.get("sep", " ")
        text = sep.join(str(a) for a in args) + end
        if sys.stdout is not None and hasattr(sys.stdout, "buffer"):
            sys.stdout.buffer.write(text.encode("utf-8", errors="replace"))
            sys.stdout.buffer.flush()

def to_json_safe(obj: Any) -> Any:
    """Recursively convert numpy/torch scalars to native Python types."""
    if obj is None or isinstance(obj, (str, bool, int)):
        return obj
    if isinstance(obj, float):
        return obj
    if hasattr(obj, "item") and callable(getattr(obj, "item", None)):
        try:
            return to_json_safe(obj.item())
        except Exception:
            pass
    if isinstance(obj, dict):
        return {str(k): to_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_json_safe(v) for v in obj]
    return str(obj)

def json_dumps(obj: Any, **kwargs: Any) -> str:
    """JSON encode with numpy-safe type coercion."""
    return json.dumps(to_json_safe(obj), **kwargs)
