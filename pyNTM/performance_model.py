"""
Backward compatibility shim.

PerformanceModel is now an alias for FlexModel, defined in pyNTM.model.
This module re-exports it so that existing code using
``from pyNTM.performance_model import PerformanceModel`` continues to work.
"""

from .model import FlexModel


class PerformanceModel(FlexModel):
    """Legacy alias for FlexModel (unified model), kept for backward compatibility."""
    pass


class Model(PerformanceModel):
    """Legacy alias for backward compatibility with pyNTM <= 1.6."""
    pass
