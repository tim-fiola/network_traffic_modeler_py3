"""
Backward compatibility shim.

_MasterModel has been merged into Model (pyNTM.model).
This module re-exports Model as _MasterModel for any code that
imports it directly.
"""

from .model import Model as _MasterModel  # noqa: F401
