"""
Backward compatibility shim.

PerformanceModel is now a subclass alias for Model, defined in pyNTM.model.
"""

from .model import Model


class PerformanceModel(Model):
    """Backward-compatible alias for Model."""
    pass
