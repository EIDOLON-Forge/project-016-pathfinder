
from __future__ import annotations

import argparse
import heapq
import math
import random
from array import array
from collections import deque
from dataclasses import dataclass

import pygame


# ============================================================
# EIDOLON #016 — PATHFINDER
# Animated Graph Search Laboratory
# ============================================================

WIDTH, HEIGHT = 1280, 800
FPS = 60

CELL = 20
COLS, ROWS = 48, 32

GRID_X, GRID_Y = 24, 116
GRID_W, GRID_H = COLS * CELL, ROWS * CELL

PANEL_X = GRID_X + GRID_W + 18
PANEL_W = WIDTH - PANEL_X - 22

BG = (6, 9, 18)
PANEL = (12, 18, 31)
PANEL_ALT = (16, 24, 40)
GRID_LINE = (26, 37, 55)
TEXT = (224, 235, 248)
MUTED = (113, 134, 159)
CYAN = (81, 240, 215)
BLUE = (75, 157, 255)
ORANGE = (255, 176, 81)
GREEN = (114, 255, 160)
RED = (255, 100, 115)
PURPLE = (184, 131, 255)

ALGORITHMS = ("A*", "Dijkstra", "BFS", "DFS")


# ============================================================
# HELPERS
# ============================================================

def clamp(value, low, high):
    return max(low, min(high, value))


def mix_color(a, b, amount):
    amount = clamp(amount, 0.0, 1.0)
    return tuple(
        int(a[i] + (b[i] - a[i]) * amount)
        for i in range(3)
    )


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def grid_to_pixel(node):
    return GRID_X + node[0] * CELL, GRID_Y + node[1] * CELL


def cell_center(node):
    x, y = grid_to_pixel(node)
    return x + CELL // 2, y + CELL // 2


# ============================================================
# AUDIO
# ============================================================

class Audio:
    def __init__(self):
        self.enabled = True
        self.ready = False
        self.cache = {}

        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(
                    frequency=22050,
                    size=-16,
                    channels=1,
                    buffer=512,
                )
            self.ready = True
            self._build_sounds()
        except pygame.error:
            self.ready = False

    def _make_tone(self, frequency, duration, volume, sweep=0):
        samples = array("h")
        rate = 22050
        count = int(rate * duration)

        for i in range(count):
            progress = i / max(1, count - 1)
            t = i / rate
            freq = max(30, frequency + sweep * progress)
            envelope = (1.0 - progress) ** 2
            value = math.sin(math.tau * freq * t) * envelope
            samples.append(int(32767 * volume * value))

        return pygame.mixer.Sound(buffer=samples.tobytes())

    def _build_sounds(self):
        self.cache["start"] = self._make_tone(420, 0.11, 0.08, 180)
        self.cache["success1"] = self._make_tone(520, 0.15, 0.08, 180)
        self.cache["success2"] = self._make_tone(690, 0.20, 0.07, 240)

    def play(self, name):
        if not self.enabled or not self.ready:
            return

        sound = self.cache.get(name)
        if sound:
            try:
                sound.play()
            except pygame.error:
                pass

    def start(self):
        self.play("start")

    def success(self):
        self.play("success1")
        self.play("success2")

    def toggle(self):
        self.enabled = not self.enabled


# ============================================================
# PATHFINDING ENGINE
# ============================================================

class Pathfinder:
    def __init__(self):
        self.start = (3, ROWS // 2)
        self.goal = (COLS - 4, ROWS // 2)

        self.walls = set()
        self.algorithm = "A*"
        self.speed = 120

        self.running = False
        self.finished = False
        self.found = False

        self.frontier = []
        self.frontier_set = set()
        self.visited = set()
        self.parent = {}
        self.cost = {}
        self.path = []

        self.expanded = 0
        self.elapsed = 0.0
        self.path_cost = 0
        self.counter = 0
        self.accumulator = 0.0

        self.reset_search()

    def neighbors(self, node):
        x, y = node

        for nx, ny in (
            (x + 1, y),
            (x - 1, y),
            (x, y + 1),
            (x, y - 1),
        ):
            nxt = (nx, ny)

            if 0 <= nx < COLS and 0 <= ny < ROWS:
                if nxt not in self.walls:
                    yield nxt

    def heuristic(self, node):
        return manhattan(node, self.goal)

    def priority(self, node):
        g = self.cost.get(node, math.inf)

        if self.algorithm == "A*":
            return g + self.heuristic(node)

        return g

    def reset_search(self):
        """Reset the search and initialize the correct queue type."""
        self.running = False
        self.finished = False
        self.found = False

        self.frontier = (
            []
            if self.algorithm in ("A*", "Dijkstra")
            else deque()
        )

        self.frontier_set = set()
        self.visited = set()
        self.parent = {}
        self.cost = {self.start: 0}
        self.path = []

        self.expanded = 0
        self.elapsed = 0.0
        self.path_cost = 0
        self.counter = 0
        self.accumulator = 0.0

        if self.algorithm in ("A*", "Dijkstra"):
            self.push_priority(self.start)
        else:
            self.frontier.append(self.start)
            self.frontier_set.add(self.start)

    def push_priority(self, node):
        self.counter += 1

        heapq.heappush(
            self.frontier,
            (self.priority(node), self.counter, node),
        )

        self.frontier_set.add(node)

    def start_search(self):
        self.reset_search()
        self.running = True

    def choose_algorithm(self, algorithm):
        if algorithm not in ALGORITHMS:
            return

        self.algorithm = algorithm
        self.reset_search()

    def reconstruct_path(self, node):
        path = [node]

        while node in self.parent:
            node = self.parent[node]
            path.append(node)

        path.reverse()
        self.path = path
        self.path_cost = len(path) - 1

    def pop_frontier(self):
        """Pop one valid node using the current algorithm's queue."""
        while self.frontier:
            if self.algorithm in ("A*", "Dijkstra"):
                _, _, node = heapq.heappop(self.frontier)
            elif self.algorithm == "BFS":
                node = self.frontier.popleft()
            else:
                node = self.frontier.pop()

            self.frontier_set.discard(node)

            if node not in self.visited:
                return node

        return None

    def step(self):
        if not self.running:
            return

        current = self.pop_frontier()

        if current is None:
            self.running = False
            self.finished = True
            self.found = False
            return

        if current == self.goal:
            self.running = False
            self.finished = True
            self.found = True
            self.reconstruct_path(current)
            return

        self.visited.add(current)
        self.expanded += 1

        for nxt in self.neighbors(current):
            if nxt in self.visited:
                continue

            new_cost = self.cost[current] + 1
            old_cost = self.cost.get(nxt, math.inf)

            if new_cost >= old_cost:
                continue

            self.cost[nxt] = new_cost
            self.parent[nxt] = current

            if self.algorithm in ("A*", "Dijkstra"):
                self.push_priority(nxt)
            elif nxt not in self.frontier_set:
                self.frontier.append(nxt)
                self.frontier_set.add(nxt)

    def update(self, dt):
        if not self.running:
            return

        self.elapsed += dt
        self.accumulator += dt * self.speed

        steps = min(400, int(self.accumulator))
        self.accumulator -= steps

        for _ in range(steps):
            if not self.running:
                break
            self.step()

    def toggle_wall(self, node):
        if node in (self.start, self.goal):
            return

        if node in self.walls:
            self.walls.remove(node)
        else:
            self.walls.add(node)

        self.reset_search()

    def clear_walls(self):
        self.walls.clear()
        self.reset_search()

    def random_maze(self, density=0.29):
        self.walls.clear()

        for y in range(ROWS):
            for x in range(COLS):
                node = (x, y)

                if node in (self.start, self.goal):
                    continue

                if random.random() < density:
                    self.walls.add(node)

        # Preserve a small clear region around both endpoints.
        for cx, cy in (self.start, self.goal):
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    node = (cx + dx, cy + dy)

                    if 0 <= node[0] < COLS and 0 <= node[1] < ROWS:
                        self.walls.discard(node)

        self.reset_search()

    def generate_maze(self):
        """Create a connected maze using randomized DFS carving."""
        self.walls = {
            (x, y)
            for x in range(COLS)
            for y in range(ROWS)
        }

        maze_start = (1, 1)
        stack = [maze_start]
        self.walls.discard(maze_start)

        while stack:
            x, y = stack[-1]
            options = []

            for dx, dy in (
                (2, 0),
                (-2, 0),
                (0, 2),
                (0, -2),
            ):
                nx, ny = x + dx, y + dy

                if 1 <= nx < COLS - 1 and 1 <= ny < ROWS - 1:
                    if (nx, ny) in self.walls:
                        options.append((nx, ny, dx, dy))

            if not options:
                stack.pop()
                continue

            nx, ny, dx, dy = random.choice(options)

            self.walls.discard((nx, ny))
            self.walls.discard((x + dx // 2, y + dy // 2))
            stack.append((nx, ny))

        self.start = (1, 1)
        self.goal = (COLS - 2, ROWS - 2)

        self.walls.discard(self.start)
        self.walls.discard(self.goal)
        self.reset_search()


# ============================================================
# APPLICATION
# ============================================================

@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    color: tuple

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt

    def draw(self, surface):
        if self.life <= 0:
            return

        radius = max(1, int(3 * min(1, self.life)))

        pygame.draw.circle(
            surface,
            self.color,
            (int(self.x), int(self.y)),
            radius,
        )


class App:
    def __init__(self, smoke_test=False):
        pygame.init()
        pygame.display.set_caption("EIDOLON #016 | PATHFINDER")

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont("consolas", 20, bold=True)
        self.medium = pygame.font.SysFont("consolas", 15, bold=True)
        self.small = pygame.font.SysFont("consolas", 12)

        self.audio = Audio()
        self.search = Pathfinder()
        self.particles = []

        self.running = True
        self.smoke_test = smoke_test
        self.smoke_elapsed = 0.0
        self.time = 0.0

        self.left_down = False
        self.right_down = False
        self.last_edit = 0
        self.success_effect_done = False

    def draw_text(self, text, font, color, pos, anchor="topleft"):
        image = font.render(str(text), True, color)
        rect = image.get_rect()
        setattr(rect, anchor, pos)
        self.screen.blit(image, rect)
        return rect

    def draw_panel(self, rect, fill=PANEL, border=GRID_LINE, radius=10):
        pygame.draw.rect(self.screen, fill, rect, border_radius=radius)
        pygame.draw.rect(
            self.screen,
            border,
            rect,
            1,
            border_radius=radius,
        )

    def node_at(self, pos):
        x, y = pos

        if not (
            GRID_X <= x < GRID_X + GRID_W
            and GRID_Y <= y < GRID_Y + GRID_H
        ):
            return None

        return (
            (x - GRID_X) // CELL,
            (y - GRID_Y) // CELL,
        )

    def set_endpoint(self, node, is_start):
        if node in self.search.walls:
            return

        if is_start:
            self.search.start = node
        else:
            self.search.goal = node

        self.search.reset_search()
        self.success_effect_done = False

    def edit_grid(self, pos, erase=False):
        node = self.node_at(pos)

        if node is None:
            return

        now = pygame.time.get_ticks()

        if now - self.last_edit < 15:
            return

        self.last_edit = now

        if erase:
            if node in self.search.walls:
                self.search.walls.remove(node)
                self.search.reset_search()
                self.success_effect_done = False
        else:
            self.search.toggle_wall(node)
            self.success_effect_done = False

    def handle_key(self, key):
        s = self.search

        if key == pygame.K_ESCAPE:
            self.running = False

        elif key == pygame.K_SPACE:
            s.start_search()
            self.success_effect_done = False
            self.audio.start()

        elif key in (pygame.K_r, pygame.K_TAB):
            s.reset_search()
            self.success_effect_done = False

        elif key == pygame.K_c:
            s.clear_walls()
            self.success_effect_done = False

        elif key == pygame.K_m:
            s.random_maze()
            self.success_effect_done = False

        elif key == pygame.K_g:
            s.generate_maze()
            self.success_effect_done = False

        elif key == pygame.K_1:
            s.choose_algorithm("A*")
            self.success_effect_done = False

        elif key == pygame.K_2:
            s.choose_algorithm("Dijkstra")
            self.success_effect_done = False

        elif key == pygame.K_3:
            s.choose_algorithm("BFS")
            self.success_effect_done = False

        elif key == pygame.K_4:
            s.choose_algorithm("DFS")
            self.success_effect_done = False

        elif key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
            s.speed = min(1500, s.speed + 40)

        elif key in (pygame.K_MINUS, pygame.K_KP_MINUS):
            s.speed = max(1, s.speed - 40)

        elif key == pygame.K_n:
            if s.running:
                s.step()

        elif key == pygame.K_v:
            self.audio.toggle()

    def handle_mouse(self, event):
        s = self.search

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.left_down = True
                node = self.node_at(event.pos)

                if node is not None and not s.running:
                    mods = pygame.key.get_mods()

                    if mods & pygame.KMOD_SHIFT:
                        self.set_endpoint(node, True)
                    elif mods & pygame.KMOD_CTRL:
                        self.set_endpoint(node, False)
                    else:
                        self.edit_grid(event.pos)

            elif event.button == 3:
                self.right_down = True
                self.edit_grid(event.pos, erase=True)

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.left_down = False
            elif event.button == 3:
                self.right_down = False

        elif event.type == pygame.MOUSEMOTION:
            if not s.running:
                if self.left_down:
                    self.edit_grid(event.pos)
                elif self.right_down:
                    self.edit_grid(event.pos, erase=True)

    def spawn_path_particles(self):
        if not self.search.found:
            return

        for node in self.search.path:
            x, y = cell_center(node)

            for _ in range(2):
                angle = random.random() * math.tau
                speed = random.uniform(15, 65)
                life = random.uniform(0.4, 1.1)

                self.particles.append(
                    Particle(
                        x=x,
                        y=y,
                        vx=math.cos(angle) * speed,
                        vy=math.sin(angle) * speed,
                        life=life,
                        color=GREEN,
                    )
                )

    def draw_header(self):
        pygame.draw.rect(self.screen, PANEL, (0, 0, WIDTH, 86))
        pygame.draw.line(self.screen, CYAN, (0, 85), (WIDTH, 85), 1)

        pygame.draw.rect(
            self.screen,
            CYAN,
            (23, 19, 3, 47),
            border_radius=2,
        )

        self.draw_text("EIDOLON", self.font, TEXT, (36, 16))
        self.draw_text(
            "PROJECT 016  /  PATHFINDER",
            self.small,
            CYAN,
            (37, 46),
        )

        s = self.search

        if s.running:
            status, status_color = "SEARCHING", CYAN
        elif s.found:
            status, status_color = "PATH FOUND", GREEN
        elif s.finished:
            status, status_color = "NO ROUTE", RED
        else:
            status, status_color = "READY", MUTED

        pygame.draw.circle(self.screen, status_color, (350, 32), 4)
        self.draw_text(status, self.small, status_color, (363, 25))

        self.draw_text(
            f"ALGORITHM  {s.algorithm}",
            self.medium,
            TEXT,
            (520, 28),
        )

        self.draw_text(
            "GRAPH SEARCH LABORATORY",
            self.small,
            MUTED,
            (WIDTH - 24, 32),
            anchor="topright",
        )

    def draw_grid(self):
        s = self.search

        pygame.draw.rect(
            self.screen,
            (8, 13, 23),
            (GRID_X, GRID_Y, GRID_W, GRID_H),
        )

        for node in s.visited:
            x, y = grid_to_pixel(node)
            pygame.draw.rect(
                self.screen,
                (19, 52, 73),
                (x + 1, y + 1, CELL - 2, CELL - 2),
            )

        for node in s.frontier_set:
            if node in s.visited:
                continue

            x, y = grid_to_pixel(node)
            pulse = (
                math.sin(self.time * 6 + node[0] * 0.2) + 1
            ) / 2

            color = mix_color(
                (26, 46, 68),
                (54, 115, 150),
                pulse,
            )

            pygame.draw.rect(
                self.screen,
                color,
                (x + 2, y + 2, CELL - 4, CELL - 4),
            )

        if s.path:
            for i, node in enumerate(s.path):
                x, y = grid_to_pixel(node)
                pulse = (
                    math.sin(self.time * 5 + i * 0.25) + 1
                ) / 2

                color = mix_color((42, 170, 148), GREEN, pulse)

                pygame.draw.rect(
                    self.screen,
                    color,
                    (x + 3, y + 3, CELL - 6, CELL - 6),
                    border_radius=4,
                )

            for a, b in zip(s.path, s.path[1:]):
                pygame.draw.line(
                    self.screen,
                    GREEN,
                    cell_center(a),
                    cell_center(b),
                    3,
                )

        for node in s.walls:
            x, y = grid_to_pixel(node)

            pygame.draw.rect(
                self.screen,
                (36, 46, 64),
                (x + 1, y + 1, CELL - 2, CELL - 2),
                border_radius=3,
            )

            pygame.draw.line(
                self.screen,
                (51, 66, 87),
                (x + 4, y + 4),
                (x + CELL - 4, y + CELL - 4),
                1,
            )

        for x in range(COLS + 1):
            px = GRID_X + x * CELL
            pygame.draw.line(
                self.screen,
                GRID_LINE,
                (px, GRID_Y),
                (px, GRID_Y + GRID_H),
                1,
            )

        for y in range(ROWS + 1):
            py = GRID_Y + y * CELL
            pygame.draw.line(
                self.screen,
                GRID_LINE,
                (GRID_X, py),
                (GRID_X + GRID_W, py),
                1,
            )

        self.draw_endpoint(s.start, CYAN, "S")
        self.draw_endpoint(s.goal, ORANGE, "G")

        pygame.draw.rect(
            self.screen,
            GRID_LINE,
            (GRID_X, GRID_Y, GRID_W, GRID_H),
            1,
        )

    def draw_endpoint(self, node, color, label):
        x, y = cell_center(node)
        pulse = (math.sin(self.time * 4) + 1) / 2
        radius = int(7 + pulse * 2)

        pygame.draw.circle(
            self.screen,
            color,
            (x, y),
            radius + 4,
            1,
        )
        pygame.draw.circle(self.screen, color, (x, y), radius)

        self.draw_text(
            label,
            self.small,
            BG,
            (x, y),
            anchor="center",
        )

    def draw_stat(self, label, value, x, y, value_color=TEXT):
        self.draw_text(label, self.small, MUTED, (x, y))
        self.draw_text(value, self.medium, value_color, (x, y + 18))

    def draw_sidebar(self):
        s = self.search
        x = PANEL_X
        y = GRID_Y

        self.draw_panel(
            pygame.Rect(x, y, PANEL_W, GRID_H),
            PANEL,
            GRID_LINE,
            radius=12,
        )

        left = x + 16
        width = PANEL_W - 32

        self.draw_text(
            "SEARCH TELEMETRY",
            self.medium,
            TEXT,
            (left, y + 17),
        )

        pygame.draw.line(
            self.screen,
            GRID_LINE,
            (left, y + 48),
            (x + PANEL_W - 16, y + 48),
        )

        self.draw_stat("NODES EXPLORED", f"{s.expanded:,}", left, y + 63, CYAN)
        self.draw_stat("FRONTIER SIZE", f"{len(s.frontier_set):,}", left, y + 115, BLUE)
        self.draw_stat(
            "ROUTE LENGTH",
            f"{s.path_cost} steps" if s.found else "--",
            left,
            y + 167,
            GREEN,
        )
        self.draw_stat("SEARCH TIME", f"{s.elapsed:.2f} s", left, y + 219, ORANGE)

        bar_y = y + 278
        self.draw_text("ALGORITHM", self.small, MUTED, (left, bar_y))

        for i, name in enumerate(ALGORITHMS):
            row_y = bar_y + 24 + i * 36
            selected = s.algorithm == name
            rect = pygame.Rect(left, row_y, width, 30)

            pygame.draw.rect(
                self.screen,
                (20, 49, 60) if selected else PANEL_ALT,
                rect,
                border_radius=6,
            )
            pygame.draw.rect(
                self.screen,
                CYAN if selected else GRID_LINE,
                rect,
                1,
                border_radius=6,
            )

            self.draw_text(
                f"{i + 1}   {name}",
                self.small,
                CYAN if selected else TEXT,
                (left + 10, row_y + 8),
            )

        speed_y = bar_y + 178

        self.draw_text("SEARCH SPEED", self.small, MUTED, (left, speed_y))
        self.draw_text(
            f"{s.speed} nodes/sec",
            self.small,
            ORANGE,
            (x + PANEL_W - 16, speed_y),
            anchor="topright",
        )

        bar = pygame.Rect(left, speed_y + 23, width, 5)
        pygame.draw.rect(self.screen, PANEL_ALT, bar, border_radius=3)

        fill = pygame.Rect(
            bar.x,
            bar.y,
            int(bar.width * clamp(s.speed / 1500, 0, 1)),
            bar.height,
        )
        pygame.draw.rect(self.screen, CYAN, fill, border_radius=3)

        instructions = [
            "SPACE   Start / restart",
            "M       Random obstacles",
            "G       Generate maze",
            "C       Clear walls",
            "+ / -   Change speed",
            "V       Toggle sound",
        ]

        info_y = speed_y + 51

        for i, instruction in enumerate(instructions):
            self.draw_text(
                instruction,
                self.small,
                TEXT if i == 0 else MUTED,
                (left, info_y + i * 20),
            )

    def draw_legend(self):
        y = HEIGHT - 33
        entries = [
            (CYAN, "START"),
            (ORANGE, "GOAL"),
            ((36, 46, 64), "WALL"),
            ((35, 95, 125), "EXPLORED"),
            (GREEN, "FINAL PATH"),
        ]

        x = GRID_X

        for color, label in entries:
            pygame.draw.rect(
                self.screen,
                color,
                (x, y + 3, 10, 10),
                border_radius=2,
            )
            self.draw_text(label, self.small, MUTED, (x + 16, y + 2))
            x += 116

        self.draw_text(
            "SHIFT + CLICK: START   CTRL + CLICK: GOAL   RIGHT CLICK: ERASE",
            self.small,
            MUTED,
            (WIDTH - 24, y + 2),
            anchor="topright",
        )

    def draw(self):
        self.screen.fill(BG)
        self.draw_header()
        self.draw_grid()
        self.draw_sidebar()

        for particle in self.particles:
            particle.draw(self.screen)

        self.draw_legend()

    def update_particles(self, dt):
        for particle in self.particles:
            particle.update(dt)

        self.particles = [
            particle
            for particle in self.particles
            if particle.life > 0
        ]

    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            self.time += dt
            self.smoke_elapsed += dt

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                elif event.type == pygame.KEYDOWN:
                    self.handle_key(event.key)

                elif event.type in (
                    pygame.MOUSEBUTTONDOWN,
                    pygame.MOUSEBUTTONUP,
                    pygame.MOUSEMOTION,
                ):
                    self.handle_mouse(event)

            self.search.update(dt)
            self.update_particles(dt)

            if self.search.finished and self.search.found:
                if not self.success_effect_done:
                    self.spawn_path_particles()
                    self.audio.success()
                    self.success_effect_done = True
            elif not self.search.finished:
                self.success_effect_done = False

            if self.smoke_test and self.smoke_elapsed >= 2.0:
                self.running = False

            self.draw()
            pygame.display.flip()

        pygame.quit()


def main():
    parser = argparse.ArgumentParser(
        description="EIDOLON #016 — Pathfinder"
    )
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Open the application briefly to test startup.",
    )

    args = parser.parse_args()
    App(smoke_test=args.smoke_test).run()


if __name__ == "__main__":
    main()
