
# EIDOLON #016 — Pathfinder

An animated pathfinding laboratory built with Python and Pygame.

Watch search algorithms explore a grid, discover routes, and reveal the difference between informed and uninformed search.

## Features

- A* search with Manhattan-distance heuristic
- Dijkstra's algorithm
- Breadth-first search (BFS)
- Depth-first search (DFS)
- Animated frontier and explored nodes
- Animated final route
- Interactive wall placement and erasing
- Movable start and goal nodes
- Random obstacle generation
- Randomized maze generation
- Adjustable search speed
- Node, frontier, time, and route statistics
- Procedural audio feedback
- Dark EIDOLON visual theme

## Requirements

- Python 3.10+
- Pygame 2.6.1

## Installation

### Windows — Git Bash

```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install -r requirements.txt
```

### Windows — PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Run

```bash
python main.py
```

## Controls

| Key / Input | Action |
|---|---|
| SPACE | Start or restart search |
| 1 | A* |
| 2 | Dijkstra |
| 3 | Breadth-first search |
| 4 | Depth-first search |
| Left-click | Place or remove walls |
| Right-click | Erase walls |
| Shift + left-click | Move start |
| Ctrl + left-click | Move goal |
| M | Generate random obstacles |
| G | Generate a maze |
| C | Clear walls |
| + / - | Increase / decrease search speed |
| V | Toggle sound |
| R / TAB | Reset search |
| ESC | Quit |

## Algorithms

### A*

A* combines the distance already traveled, `g(n)`, with a heuristic estimate of the remaining distance, `h(n)`.

`f(n) = g(n) + h(n)`

With a four-direction grid and unit movement costs, Manhattan distance is an admissible heuristic.

### Dijkstra

Dijkstra prioritizes the lowest known travel cost. With equal movement costs, it finds a shortest path but usually explores more nodes than A*.

### Breadth-first search

BFS explores the graph level by level. It finds a shortest path when all edges have equal cost.

### Depth-first search

DFS explores deeply before backtracking. It can find a route, but it does not guarantee a shortest path.

## Smoke Test

```bash
python main.py --smoke-test
```

## Project

EIDOLON #016 — Pathfinder

Part of the EIDOLON journey to build 500+ projects across programming, algorithms, simulations, graphics, AI, cybersecurity, and engineering.

Build. Experiment. Break. Repeat.
