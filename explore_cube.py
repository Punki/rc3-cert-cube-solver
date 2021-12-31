#!/usr/bin/env python3
# coding: utf-8

#
# Explorer bot for the rc3 CERT Cube maze.
# Uses an existing Selenium webdriver browser window to walk through all rooms in the maze.
# Saves the explored rooms and connections in a JSON file.
#


from collections import deque
import datetime
import json
import re
import shutil
import sys
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

# each room has four exits (ie. directions) which can be explored:
DIR_UP = "u"
DIR_DOWN = "d"
DIR_LEFT = "l"
DIR_RIGHT = "r"

# the order in this tuple also sets the order in which directions are explored:
allDirections = (DIR_UP, DIR_RIGHT, DIR_DOWN, DIR_LEFT)


class CubeRooms:
    """Manages information about the rooms and connections in the cube."""

    def __init__(self, jsonFile):
        "jsonFile: the file from which to load initial rooms, and where new information will be written to."
        self.jsonFile = jsonFile
        self.rooms = {}

        # load rooms from JSON file, if possible:
        try:
            fp = open(self.jsonFile)
            loadedRooms = json.load(fp)
            fp.close()
            for rId in loadedRooms:
                self.rooms[int(rId)] = {}
                for d in loadedRooms[rId]:
                    self.rooms[int(rId)][d] = loadedRooms[rId][d]
        except:
            print("no rooms loaded")
        else:
            print(f"loaded {len(self.rooms)} start rooms")
            self._save()  # save loaded data again, to get a nicely formatted file

    def addRoom(self, startRoom, direction, resultRoom):
        """
        Adds a connection from startRoom: going in the indicated direction leads into resultRoom.
        startRoom and resultRoom must be integer room ids.
        """
        assert direction in allDirections

        if not (startRoom in self.rooms):
            self.rooms[startRoom] = {}
        if direction in self.rooms[startRoom]:
            print(f"this result ({startRoom},{direction} -> {resultRoom}) already exists")
            if self.rooms[startRoom][direction] != resultRoom:
                print(
                    f"ERROR: new result ({startRoom},{direction} -> {resultRoom}) does not match previous result ({startRoom},{direction} -> {self.rooms[startRoom][direction]})!")
                sys.exit(1)
            else:
                return

        self.rooms[startRoom][direction] = resultRoom
        self._save()

    def get(self, room):
        """
        Returns a dict of known connections from the specified room.
        Dict keys are the directions; values are the target rooms.
        """
        if not (room in self.rooms):
            return {}
        return self.rooms[room]

    def _save(self):
        """Saves the current room graph to file, and creates a backup."""
        with open(self.jsonFile, "w") as fp:
            json.dump(self.rooms, fp, indent=4)

        backupName = "%s.%s.json" % (self.jsonFile, datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
        shutil.copyfile(self.jsonFile, backupName)

    def find_shortest_path(self, start, end):
        """
        Returns the shortest (?) path between two nodes in the room graph.
        The path is in a weird nested format and should be "unwrapped" before use.

        Based on the code by Eryk Kopczyński from https://www.python.org/doc/essays/graphs/
        """
        dist = {start: [(start, "")]}
        q = deque([start])
        while len(q):
            at = q.popleft()
            for d in self.rooms[at]:
                next = self.rooms[at][d]
                if next not in dist:
                    dist[next] = [dist[at], (next, d)]
                    q.append(next)
        return dist.get(end)

    def getPathToNextIncomplete(self, startRoom):
        """Returns the path to the next room where at least one direction has not yet been explored."""

        def unwrap(p):
            if isinstance(p, list):
                return unwrap(p[0]) + p[1:]
            else:
                return [p]

        targetPath = None
        for targetRoom in self.rooms:
            if len(self.rooms[targetRoom]) < 4:
                print("candidate: ", targetRoom)
                path = unwrap(self.find_shortest_path(startRoom, targetRoom))[1:]
                if path and (targetPath is None or len(path) < len(targetPath)):
                    targetPath = path

        if targetPath is None:
            print("all rooms are complete!")
            return None

        print("shortest path to incomplete room:", targetPath)
        return targetPath


if len(sys.argv) != 4:
    print(f"Usage: {sys.argv[0]} <room graph JSON file> <Selenium webdriver URL> <Selenium webdriver session id>")
    sys.exit(1)

roomJsonFile = sys.argv[1]
driverUrl = sys.argv[2]
driverSession = sys.argv[3]

rooms = CubeRooms(roomJsonFile)

driver = webdriver.Remote(command_executor=driverUrl, desired_capabilities={})
driver.close()  # this prevents the dummy browser
driver.session_id = driverSession


def getRoomId(url):
    """Extracts the room id (as integer) from a room URL."""
    return int(re.search(r"(\d+)\.json", url).group(1))


# walk through the maze:
while True:
    oldUrl = driver.current_url
    startId = getRoomId(oldUrl)
    print("old room:", startId)

    knownResults = rooms.get(startId)
    print("have already explored %d directions from here (%s)" % (len(knownResults), ",".join(knownResults.keys())))
    nextDir = None
    for d in allDirections:
        if d not in knownResults:
            nextDir = d
            break
    if nextDir is None:
        print(f"have already explored all directions of {startId}!")
        path = rooms.getPathToNextIncomplete(startId)
        print("path to next goal:", path)
        nextDir = path[0][1]

    print("next direction:", nextDir)

    # set up Selenium "action chains" which can be executed to walk into the specified direction:
    cv = driver.find_element(By.TAG_NAME, "canvas")

    actionChains = {DIR_UP: ActionChains(driver)}
    actionChains[DIR_UP].click(cv).key_down(Keys.SHIFT).key_down(Keys.ARROW_UP)
    actionChains[DIR_DOWN] = ActionChains(driver)
    actionChains[DIR_DOWN].click(cv).key_down(Keys.SHIFT).key_down(Keys.ARROW_DOWN)
    actionChains[DIR_LEFT] = ActionChains(driver)
    actionChains[DIR_LEFT].click(cv).key_down(Keys.SHIFT).key_down(Keys.ARROW_LEFT)
    actionChains[DIR_RIGHT] = ActionChains(driver)
    actionChains[DIR_RIGHT].click(cv).key_down(Keys.SHIFT).key_down(Keys.ARROW_RIGHT)

    actionChains[nextDir].perform()

    # wait for a few seconds until room URL has changed:
    for i in range(10):
        newUrl = driver.current_url
        # print("OlD Room: ", getRoomId(oldUrl), "NEW Room: ",  getRoomId(newUrl))
        if getRoomId(newUrl) != getRoomId(oldUrl):
            break
        print("waiting a bit more...")
        time.sleep(0.2)
    else:
        print(startId, nextDir, "leads again to", startId, " !")
        sys.exit(1)

    rooms.addRoom(startId, nextDir, getRoomId(newUrl))
    time.sleep(0.2)
