"""
History Feature Module
Provides time-series analysis with filtering, stacking, and grouping controls
"""
from features.history.layout import create_history_layout
from features.history import callbacks  # Import to register callbacks

__all__ = ['create_history_layout', 'callbacks']
