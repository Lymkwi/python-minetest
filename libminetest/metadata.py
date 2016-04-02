#!/usr/bin/env python3
# -*- encoding: utf8 -*-
###########################
## Metadata for Python-MT
##
##
#

from .inventory import InvRef
from .utils import Pos


class NodeMetaRef:
    """Class made to contain a node's metadata and interact with it"""
    def __init__(self, spos = None, meta = None, inv = None):
        """
        Constructor for NodeMetaRef.

        Arguments :
         - spos, keyword, defaults to None, is the node's position
         - meta, keyword, defaults to None, is a dictionary of metadata to be loaded
         - inv, keyword, defaults to None, is an InvRef of the node's inventory to be loaded
        """

        self.data = meta or dict()
        self.pos = spos or Pos(0, 0, 0)
        self.inv = inv or InvRef()

    def get_raw(self, key):
        """
        Return the raw value stored (or not) in the object's data dictionary

	Arguments :
         - key, mandatory, is the name of the data to get

	Returns : any object that could have been stored along with the provided key or None if no value found
        """

        return self.data.get(key)

    def set_raw(self, key, val):
        """
        Store a value in the object's data dictionary

	Arguments :
         - key, mandatory, is the name of the data to store
         - val, mandatory, is the value to store
        """

        self.data[key] = val

    def get_string(self, key):
        """
        Return the string value stored (or not) in the object's data dictionary

	Arguments :
	 - key, mandatory, is the name of the data to get as a string

	Returns : str or None if no value found
	"""

        # Gather the integers into a string
        data = self.data.get(key)
        if not data:
            return None

        res = ""
        for c in data:
            if c >= 256 or c < 0:
                return data # IT IS A NUMBER AAAAAH

            res += chr(c)
        return res

    def set_string(self, key, val):
        """
        Store a string value in the object's data dictionary

	Arguments :
	 - key, mandatory, is the name of the string data to store
         - val, mandatory, is the string value to store
	"""

        self.data[key] = [ord(b) for b in val]

    def get_int(self, key):
        """
	Return integer value stored (or not) in the data dictionary

	Arguments :
	 - key, mandatory, is the name of the integer value stored (or not)

	Returns : int or None if no value found
        """

        return int(self.data.get(key))

    def set_int(self, key, val):
        """
	Store an integer value in the object's data dictionary

	Arguments :
	 - key, mandatory, is the name of the integer value to store
	 - val, mandatory, is the integer value to store
	"""

        self.data[key] = int(val)

    def get_float(self, key):
        """
	Return a float value stored (or not) in the object's data dictionary

	Arguments :
	 - key, mandatory, is the name of the float value stored (or not)

	Returns : float or None if no value found
	"""

        return float(self.data.get(key))

    def set_float(self, key, val):
        """
	Store a float value in the object's data dictionary

	Arguments :
	 - key, mandatory, is the name of the float value to store
	 - val, mandatory, is the float value to store
	"""

        self.data[key] = float(val)

    def get_inventory(self):
        """
	Return the InvRef object, reference to the node's inventory

	Returns : libminetest.inventory.InvRef
	"""

        return self.inv

    def to_table(self):
        """
	Returns the object's data dictionary

	Returns : dict
        """

        return self.meta

    def from_table(self, tab = {}):
        """
	Import and deserialize a metadata dictionary to be used by the object
        """
        self.meta = tab
