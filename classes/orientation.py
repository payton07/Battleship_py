# -*- coding: utf-8 -*-
class Orientation(object):
    HORIZONTAL = 1
    VERTICAL = 2
    
    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        if isinstance(other, Orientation):
            return self.value == other.value
        return self.value == other

    def __repr__(self):
        return "HORIZONTAL" if self.value == 1 else "VERTICAL"
