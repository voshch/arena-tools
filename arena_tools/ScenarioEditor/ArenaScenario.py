import numpy as np
import os
import yaml
import json
from .Pedestrian.Pedestrian import Pedestrian
from ..utils.HelperFunctions import *


class ArenaScenario:
    def __init__(self):
        self.pedestrianAgents = []  # list of PedestrianAgent objects
        self.interactiveObstacles = []  # list of InteractiveObstacle messages
        self.staticObstacles = []  # list of 
        self.robotPosition = np.zeros(2)  # starting position of robot
        self.robotGoal = np.zeros(2)  # robot goal
        self.mapPath = ""  # path to map file
        self.resets = 0
        self.path = ""  # path to file associated with this scenario

    def toDict(self):
        d = {}

        d["pedestrian_agents"] = [a.toDict() for a in self.pedestrianAgents]
        d["static_obstacles"] = [o.toDict() for o in self.staticObstacles]
        # d["interactive_obstacles"] = TODO...
        d["robot_position"] = [float(value) for value in self.robotPosition]
        d["robot_goal"] = [float(value) for value in self.robotGoal]
        d["resets"] = self.resets
        d["format"] = "arena-tools"

        return d

    @staticmethod
    def fromDict(d: dict):
        scenario = ArenaScenario()
        scenario.loadFromDict(d)
        return scenario

    def loadFromDict(self, d: dict):
        self.pedestrianAgents = [Pedestrian.fromDict(
            a) for a in d["pedestrian_agents"]]
        # self.interactiveObstacles = ...TODO
        self.robotPosition = np.array(
            [d["robot_position"][0], d["robot_position"][1]])
        self.robotGoal = np.array([d["robot_goal"][0], d["robot_goal"][1]])
        if ("resets") in d.keys():
            self.resets = d["resets"]
        else:
            self.resets = 0

    def saveToFile(self, path_in: str = "") -> bool:
        '''
        Save Scenario in file.
        - path_in: path to save file
        - format: format of save file, can be "json" or "yaml"
        '''
        if os.path.exists(path_in):  # TODO is this not always false when it's a new filename?
            self.path = path_in

        if self.path == "":
            return False

        _, file_extension = os.path.splitext(self.path)
        with open(self.path, "w") as file:
            data = self.toDict()
            if file_extension == ".json":
                json.dump(data, file, indent=4)
            elif file_extension == ".yaml":
                yaml.dump(data, file, default_flow_style=None)
            else:
                raise Exception(
                    "wrong format. file needs to have 'json' or 'yaml' file ending.")

        return True

    def loadFromFile(self, path_in: str):
        if os.path.exists(path_in):
            _, file_extension = os.path.splitext(path_in)
            with open(path_in, "r") as f:
                data = None
                if file_extension == ".json":
                    data = json.load(f)
                elif file_extension == ".yaml":
                    data = yaml.safe_load(f)
                else:
                    raise Exception(
                        "wrong format. file needs to have 'json' or 'yaml' file ending.")

                self.loadFromDict(data)
                self.path = path_in

        else:
            raise Exception(f"file '{path_in}' does not exist")
