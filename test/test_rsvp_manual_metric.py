# TODO - add the unit tests for rsvp manual metric for both Flex and Performance Models

# 2 parallel LSPs source-dest, but one with a lower than default metric;
# traffic should only take lower metric LSP

# 1 LSP source-dest, but with higher than default metric;
# traffic should take that LSP due to better protocol preference;
# if that LSP fails, IGP routing

# 2 parallel LSPs source-dest, one with more hops than the other;
# the one with fewer hops has the highest metric; traffic should
# take the lower-metric LSP

# 2 parallel LSPs source-dest, both with higher than default metric, but
# one LSP with a higher metric than the other.  Traffic should take lower
# metric LSP
