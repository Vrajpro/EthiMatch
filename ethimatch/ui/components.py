"""Professional UI components for EthiMatch (backward-compatible facade)."""

from ui.presentation._utils import *  # noqa: F403
from ui.presentation.chart_style import *  # noqa: F403
from ui.presentation.charts import *  # noqa: F403
from ui.presentation.layout import *  # noqa: F403
from ui.presentation.verdict import *  # noqa: F403
from ui.presentation.clinical import *  # noqa: F403
from ui.presentation.registry import *  # noqa: F403
from ui.presentation.matching import *  # noqa: F403
from ui.presentation.cohort import *  # noqa: F403

# ``import *`` omits leading-underscore names; re-export private helpers explicitly.
from ui.presentation._utils import (  # noqa: F401
    _esc,
    _matching_fmt,
    _md_inline,
    _records_to_dataframe,
    _short_patient_id,
)
from ui.presentation.chart_style import (  # noqa: F401
    _academic_bar_marker,
    _apply_publication_layout,
    _chart_font,
    _criteria_legend_traces,
    _verdict_bar_outline,
    _verdict_chart_color,
)
from ui.presentation.charts import _render_benchmark_png_export  # noqa: F401
from ui.presentation.clinical import _conf_bar, _rule_row, _src_badge  # noqa: F401
from ui.presentation.registry import (  # noqa: F401
    _COHORT_REGISTRY_COLS,
    _COHORT_REGISTRY_WEIGHTS,
    _MATCHING_REGISTRY_COLS,
    _MATCHING_REGISTRY_WEIGHTS,
    _cohort_row_fields,
    _matching_row_fields,
    _registry_page_slice,
    _render_registry_data_row,
    _render_registry_header,
    _render_registry_pagination,
    _registry_toggle_box,
)
from ui.presentation.verdict import (  # noqa: F401
    _matching_verdict_sort_order,
    _registry_verdict_css,
)
