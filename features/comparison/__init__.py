"""
Comparison Feature Module
Handles comparison tab functionality including layout, callbacks, charts, and business logic

This module provides:
- UI layout for the comparison tab
- Interactive callbacks for data updates and exports
- Chart generation functions for various comparison visualizations
- Business logic for data processing and analysis text generation
- LLM-powered financial analysis (optional, requires Azure OpenAI)

Usage:
    from features.comparison import create_comparison_layout
    from features.comparison.callbacks import (
        populate_comparison_dates,
        update_comparison_filter_values,
        update_enhanced_comparison_content,
        export_comparison_excel,
        export_comparison_png,
        save_comparison
    )
"""

from .layout import create_comparison_layout
from .llm_financial_analyst import FinancialAnalystLLM, analyze_comparison_with_llm
from .logic import prepare_type_breakdown_data, generate_enhanced_comparison_text_updated
from .charts import (
    create_comparison_heatmap,
    create_dumbbell_chart_updated,
    create_division_stacked_chart,
    create_type2_breakdown_charts,
    create_comparison_chart,
    create_ratio_comparison_chart
)

# Import callbacks to register them with Dash
# Note: These are imported but not exported to __all__ since they auto-register via decorators
from . import callbacks

__all__ = [
    # Layout
    'create_comparison_layout',

    # LLM Analysis
    'FinancialAnalystLLM',
    'analyze_comparison_with_llm',

    # Business Logic
    'prepare_type_breakdown_data',
    'generate_enhanced_comparison_text_updated',

    # Charts
    'create_comparison_heatmap',
    'create_dumbbell_chart_updated',
    'create_division_stacked_chart',
    'create_type2_breakdown_charts',
    'create_comparison_chart',
    'create_ratio_comparison_chart',
]
