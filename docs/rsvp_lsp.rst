RSVP LSP
========




In a live simulation, if you want to remove a manual metric for an LSP, set the LSP's manual_metric attribute to -1.
This will clear the manual metric and the LSP will then inherit the default metric (that of the shortest IGP path from
the LSP source node to the destination node).