"""A Circuit object in a Model. Circuit is comprised of two Interface objects"""


class Circuit(object):
    """A circuit is an object consisting of 2 connected interfaces """

    def __init__(self, interface_a, interface_b):
        self.interface_a = interface_a
        self.interface_b = interface_b

    def __repr__(self):
        return 'Circuit(%r, %r)' \
               % (self.interface_a,
                  self.interface_b,)

    def _key(self):
        return (self.interface_a._key, self.interface_b._key)

    def get_circuit_interfaces(self, model):
        """
        Return the circuit's interface objects
        """
        return (self.interface_a, self.interface_b)
