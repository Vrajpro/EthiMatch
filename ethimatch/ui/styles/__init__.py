"""CSS asset loading for EthiMatch theme."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

_STYLES_DIR = Path(__file__).resolve().parent

@lru_cache(maxsize=1)
def _read_css(name: str) -> str:
    return (_STYLES_DIR / name).read_text(encoding="utf-8")

CSS = f"<style>\n{_read_css('clinical.css')}\n</style>"

def get_theme_css() -> str:
    from config import theme_css_variables

    theme_root = f"""
<style>
:root {{
{theme_css_variables()}
  --success: var(--status-pass);
  --success-bg: var(--status-pass-bg);
  --warning: var(--status-inconclusive);
  --warning-bg: var(--status-inconclusive-bg);
  --danger: var(--status-fail);
  --danger-bg: var(--status-fail-bg);
  --info: var(--status-neutral);
  --info-bg: var(--status-neutral-bg);
}}
</style>
"""
    return theme_root + CSS
