import unittest

from pyNTM import Model
from pyNTM import Parallel_Link_Model


# Test cases
# - LSPs won't transit over non-rsvp_enabled interface on both models
# - percent_reserved_bandwidth limits amount of reservable_bandwidth on Interface
#       - test return self._reservable_bandwidth on Interface
# - try manually setting reservable_bandwidth on an interface


