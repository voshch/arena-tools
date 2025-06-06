import numpy as np

from arena_tools.utils.HelperFunctions import normalize_angle


class FlatlandObject():
    def __init__(self, name: str = ""):
        self.name = name
        self.pos = np.zeros(2)
        self.angle = 0.0

    @staticmethod
    def fromDict(d: dict):
        o = FlatlandObject()
        o.loadFromDict(d)
        return o

    def loadFromDict(self, d: dict):
        self.name = d["name"]
        self.pos = np.array([float(val) for val in d["pos"]])
        self.angle = float(d["angle"])

    def toDict(self):
        d = {}
        d["name"] = self.name
        d["pos"] = [float(val) for val in self.pos]
        d["angle"] = round(normalize_angle(self.angle), 3)
        return d
