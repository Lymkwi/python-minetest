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
            newlists[params[1]] = {}
            expectation = int(params[2])
            expected_type = "ItemStack"
            current_listname = params[1]

        elif params[0] == "Width":
            if expected_type == "ItemStack":
                continue

        elif params[0] == "Empty" or params[0] == "Item":
            if expectation > 0:
                expectation -= 1
            else:
                raise InventoryDeserializationError("Unexpected Item (line {0})".format(lines.index(line)+1))

            newlists[current_listname][expectation] = ItemStack(" ".join(params[1:]))

        elif params[0] == "EndInventoryList":
            if expectation > 0:
                raise InventoryDeserializationError("Too few items for list {0}".format(current_listname))

            expected_type = "ItemStack"

            # Reverse everything
            new_current_list = dict()
            new_current_list_size = len(newlists[current_listname])
            for i in newlists[current_listname]:
                new_current_list[new_current_list_size - i - 1] = newlists[current_listname][i]

            newlists[current_listname] = new_current_list
            current_listname = ""

    return newlists



class ItemStack:
    def __init__(self, deft):
        if not deft or deft == "":
            self.name = ""
            self.count = 0

        elif type(deft) == type("str"):
            self.deserialize(deft)

        elif type(deft) == type({}):
            self.name = deft["name"]
            self.count = deft["count"]

    def deserialize(self, serializat):
        params = serializat.split(' ')
        self.name = params[0]
        if len(params) > 1:
            self.count = int(params[1])
        else:
            self.count = 0

    def get_name(self):
        return self.name

    def get_count(self):
        return self.count


class InvRef:
    def __init__(self, fields = {}):
        self.lists = fields

    def from_string(self, serializat):
        self.lists = deserializeInventory(serializat)

    def from_list(self, lists):
        self.lists = lists

    def to_string(self):
        data = StringIO("")

        for list_name in self.lists:
            data.write("List {0} {1}\n".format(list_name, len(self.lists[list_name])))
            data.write("Width 0\n")

            for id in range(len(self.lists[list_name])):
                stack = self.lists[list_name].get(id)
                if stack.get_name() == "":
                    data.write("Empty\n")
                else:
                    data.write("Item {0} {1}\n".format(stack.get_name(), stack.get_count()))

            data.write("EndInventoryList\n")


        data.write("EndInventory\n")

        return data.getvalue()
