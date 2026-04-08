"""
Backward compatibility shim.

FlexModel is now defined in pyNTM.model.  This module re-exports it
so that existing code using ``from pyNTM.flex_model import FlexModel``
continues to work.
"""

from .model import FlexModel  # noqa: F401


class Parallel_Link_Model(FlexModel):
    """Legacy alias for FlexModel, kept for backward compatibility."""
    pass
