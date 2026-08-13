"""Torch device resolution — prefer CUDA GPU when available."""

from __future__ import annotations

from console import safe_print

def resolve_torch_device(requested: int | None = None) -> int:
    """Return HuggingFace pipeline device index.

    * ``requested >= 0`` — use that GPU index explicitly.
    * ``requested == -1`` or ``None`` — auto: CUDA GPU 0 if available, else CPU (-1).
    """
    if requested is not None and requested >= 0:
        return requested

    try:
        import torch

        if torch.cuda.is_available():
            name = torch.cuda.get_device_name(0)
            safe_print(f"[Device] CUDA available — using GPU: {name}")
            return 0
    except ImportError:
        pass

    return -1
