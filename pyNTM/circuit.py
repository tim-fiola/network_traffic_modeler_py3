"""A Circuit object in a Model. Circuit is comprised of two Interface objects"""


class Circuit(object):
    """A circuit is an object consisting of 2 connected interfaces """

    def __init__(self, interface_a, interface_b):
        """
        Initialize the interface.

        Args:
            self: (todo): write your description
            interface_a: (str): write your description
            interface_b: (str): write your description
        """
        self.interface_a = interface_a
        self.interface_b = interface_b

    def __repr__(self):
        """
        Return a human - readable representation of this interface.

        Args:
            self: (todo): write your description
        """
        return 'Circuit(%r, %r)' \
               % (self.interface_a,
                  self.interface_b,)

    def _key(self):
        """
        The public key for the interface

        Args:
            self: (todo): write your description
        """
        return (self.interface_a._key, self.interface_b._key)

    def get_circuit_interfaces(self, model):
        """
        Return the Circuit's component Interface objects in model object

        :param model: model object containing Circuit
        :return: Component Interfaces in Circuit
        """
        return (self.interface_a, self.interface_b)

    def failed(self, model):
        """
        Is Circuit failed?

        :param model: Model containing circuit
        :return: Boolean
        """
        int_a, int_b = self.get_circuit_interfaces(model)
        if int_a.failed or int_b.failed:
            return True
        else:
            return False
