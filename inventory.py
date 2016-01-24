#!/usr/bin/env python3
# -*- encoding: utf8 -*-
###########################
## Inventory for Python-MT
##
##
#

from io import StringIO

from errors import InventoryDeserializationError
from utils import readU8

def getSerializedInventory(strm):
    # serialized inventory
    inv = "".join([chr(readU8(strm)) for _ in range(len(b"EndInventory\n"))])
    while not "EndInventory\n" in inv:
        inv += chr(readU8(strm))

    return inv


def deserializeInventory(serializat):
    newlists = {}
    lines = serializat.split('\n')
    expectation = 0
    current_listname = ""
    expected_type = None

    for line in lines:
        params = line.split(' ')

        if params[0] == "":
            # EOF
            break

        elif params[0] == "List":
            newlists[params[1]] = []
            expectation = int(params[2])
            expected_type = "ItemStack"
            current_listname = params[1]

        elif params[0] == "Empty" or params[0] == "Item":
            if expectation > 0:
                expectation -= 1
            else:
                raise InventoryDeserializationError("Unexpected Item (line {0})".format(lines.index(line)+1))

            newlists[current_listname].append(ItemStack("".join(params[1:] or [])))

        elif params[0] == "EndInventoryList":
            if expectation > 0:
                raise InventoryDeserializationError("Too few items for list {0}".format(current_listname))

            expected_type = "ItemStack"
            current_listname = ""

    return newlists



class ItemStack:
    def __init__(self, deft):
        if not deft:
            self.name = ""
            self.count = 0

        elif type(deft) == type("str"):
            self.deserialize(deft)

        elif type(deft) == type({}):
            self.name = deft["name"]
            self.count = deft["count"]

    def deserialize(self, serializat):
        pass



class InvRef:
    def __init__(self, fields = {}):
        self.lists = fields

    def from_string(self, serializat):
        self.lists = deserializeInventory(serializat)

    def from_list(self, lists):
        self.lists = lists
