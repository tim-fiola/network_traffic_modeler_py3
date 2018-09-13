"""A class to represent an RSVP label-switched-path in the network model """

class RSVP_LSP(object):
    """A class to represent an RSVP label-switched-path in the network model """
    
    def __init__(self, model, source_node_name, dest_node_name, lsp_name = 'none', 
            reserved_bw = 0):
        self.model = model 
        self.source_node_name = source_node_name
        self.dest_node_name = dest_node_name
        self.lsp_name = lsp_name
        self.reserved_bw = reserved_bw
        
        # Validate the reserved bandwidth
        if not(isinstance(reserved_bw, (int, float)):
            raise ValueError("reserved_bw must be an int or float")
            
    # Get candidate paths
    
    
    # Select a candidate path that can accomodate the reserved bandwidth
    
    
    # Reset the reserved bandwidth value (resignal reserved bandwidth)
        # How much traffic am I carrying?
        # Is there an available path with capacity for my reserved bandwidth
    
    # Calculate carried traffic
    
    
    
    # Return the demands carried by the LSP and how much traffic per demand
