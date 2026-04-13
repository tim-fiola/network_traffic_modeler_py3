"""
Backward compatibility shim.

FlexModel is now a subclass alias for Model, defined in pyNTM.model.
"""

from .model import Model


class FlexModel(Model):
    """Backward-compatible alias for Model."""

    pass


class Parallel_Link_Model(FlexModel):
    """Legacy alias for Model, kept for backward compatibility."""

    pass
