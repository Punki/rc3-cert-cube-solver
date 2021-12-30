#!/usr/bin/env python3

#
# Creates a Dot graph of the rooms in the rc3 CERT Cube maze.
# Also, prints some statistics about the room graph.
#

import graphviz
import json
import sys


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <room graph JSON file> <Dot graph output file>")
        sys.exit(1)

    inFile = sys.argv[1]
    outFile = sys.argv[2]

    with open(inFile) as fp:
        rooms = json.load(fp)
    print(f"loaded {len(rooms)} rooms")

    dot = graphviz.Digraph()

    buckets = []
    for i in range(5):
        buckets.append([])

    numEdges = 0
    for key in rooms:
        startRoom = int(key)
        dot.node(str(startRoom))

        numDirs = len(rooms[key])
        buckets[numDirs].append(startRoom)

        for d in rooms[key]:
            resultRoom = rooms[key][d]
            dot.edge(str(startRoom), str(resultRoom), label=d)
            numEdges+=1

    print(f"have {numEdges} room connections")

    # display how many rooms and directions have been explored so far:
    for i in range(5):
        print(f"{i} directions explored: {len(buckets[i])} rooms ({buckets[i]})")

    with open(outFile, "w") as fp:
        fp.write(dot.source)

    print("Convert to PNG image eg. with:")
    print(f"sfdp -x -Goverlap=scale -Tpng {outFile} > graph.png")
