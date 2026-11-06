import random

DIRS = [(0, -1), (1, 0), (0, 1), (-1, 0)]   # up, right, down, left as (dx, dy); y grows downwards
TURN = [0, -1, +1]                          # action 0 = straight, 1 = left, 2 = right


def dist(a, b):
    """Manhattan distance between two cells."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


class CompetitiveSnake:
    """12x12 field, 2 apples, and a rival snake run by the computer.

    The rival goes to the nearest apple in 70% of moves and moves randomly in 30%;
    it never hits a wall or itself. We die if we hit a wall, ourselves or the rival
    (head-on too). A dead rival respawns elsewhere. The game lasts 300 moves,
    the score is the number of apples WE ate.
    """

    def __init__(self, seed=None, size=12, n_apples=2, max_steps=300):
        self.size, self.n_apples, self.max_steps = size, n_apples, max_steps
        self.rng = random.Random(seed)       # same seed = same game
        mid = size // 2
        self.direction = 1                   # looking right
        self.snake = [(3, mid), (2, mid), (1, mid)]   # head first
        self.rival, self.apples = [], []
        self.score = self.steps = 0
        self.space_cache, self.space_step = {}, -1    # memory for free_space()
        self.spawn_rival()
        self.fill_apples()

    # World
    def inside(self, cell):
        return 0 <= cell[0] < self.size and 0 <= cell[1] < self.size

    def blocked(self, cell):
        """A snake dies if it enters this cell."""
        return not self.inside(cell) or cell in self.snake or cell in self.rival

    def fill_apples(self):
        while len(self.apples) < self.n_apples:
            free = [(x, y) for x in range(self.size) for y in range(self.size)
                    if not self.blocked((x, y)) and (x, y) not in self.apples]
            self.apples.append(self.rng.choice(free))

    def spawn_rival(self):
        """A new rival of length 3 on a free spot, at least 4 cells away from us."""
        for _ in range(200):
            head, d = (self.rng.randrange(self.size), self.rng.randrange(self.size)), self.rng.randrange(4)
            body = [(head[0] - k * DIRS[d][0], head[1] - k * DIRS[d][1]) for k in range(3)]
            if all(not self.blocked(c) for c in body) and dist(head, self.snake[0]) >= 4:
                self.rival = body
                return
        self.rival = [(self.size - 1, self.size - 1)]

    def rival_move(self):
        """The rival's new head cell, or None if it is stuck."""
        hx, hy = self.rival[0]
        options = [(hx + dx, hy + dy) for dx, dy in DIRS]
        options = [c for c in options if self.inside(c) and c not in self.rival]
        if not options:
            return None
        if self.rng.random() < 0.7:          # 70%: go for the nearest apple
            target = min(self.apples, key=lambda a: dist(a, self.rival[0]))
            best = min(dist(c, target) for c in options)
            options = [c for c in options if dist(c, target) == best]
        return self.rng.choice(options)      # 30%: any free move

    def step(self, action):
        """Make one move. Returns (ate, died)."""
        self.direction = (self.direction + TURN[action]) % 4
        new_head = self.next_cell(0)
        rival_head = self.rival_move()
        self.steps += 1

        if self.blocked(new_head) or new_head == rival_head:     # wall, ourselves, rival, head-on
            return False, True

        self.snake.insert(0, new_head)
        ate = new_head in self.apples
        if ate:                              # the tail stays, so we grow
            self.apples.remove(new_head)
            self.score += 1
        else:
            self.snake.pop()

        if rival_head is None or rival_head in self.snake:       # the rival dies and respawns
            self.rival = []
            self.spawn_rival()
        else:
            self.rival.insert(0, rival_head)
            if rival_head in self.apples:                        # the rival steals an apple
                self.apples.remove(rival_head)
            else:
                self.rival.pop()
        self.fill_apples()
        return ate, False

    # What the agent can look at
    def head(self):
        return self.snake[0]

    def length(self):
        return len(self.snake)

    def heading(self):
        """Where we look, as (dx, dy)."""
        return DIRS[self.direction]

    def rival_head(self):
        return self.rival[0]

    def dist(self, a, b):
        return dist(a, b)

    def next_cell(self, turn, k=1):
        """The cell k steps from the head after a turn (0 = straight, 1 = left, 2 = right)."""
        dx, dy = DIRS[(self.direction + TURN[turn]) % 4]
        return (self.snake[0][0] + k * dx, self.snake[0][1] + k * dy)

    def cell_ahead(self, k=1):
        return self.next_cell(0, k)

    def cell_left(self, k=1):
        return self.next_cell(1, k)

    def cell_right(self, k=1):
        return self.next_cell(2, k)

    def danger_straight(self):
        return int(self.blocked(self.cell_ahead()))

    def danger_left(self):
        return int(self.blocked(self.cell_left()))

    def danger_right(self):
        return int(self.blocked(self.cell_right()))

    def food_list(self):
        """Apples sorted by distance to our head, nearest first."""
        return sorted(self.apples, key=lambda a: dist(a, self.snake[0]))

    def food_distance(self):
        return dist(self.food_list()[0], self.snake[0])

    def food_direction(self, k=0):
        """4 bits: is the k-th nearest apple above / right of / below / left of the head?"""
        (hx, hy), (fx, fy) = self.snake[0], self.food_list()[k]
        return (int(fy < hy), int(fx > hx), int(fy > hy), int(fx < hx))

    def my_direction(self):
        """4 bits: where the head looks (up, right, down, left)."""
        return tuple(int(self.direction == d) for d in range(4))

    def rival_head_near(self, radius):
        """1 if the rival's head is within `radius` cells of ours."""
        return int(dist(self.rival[0], self.snake[0]) <= radius)

    def rival_food_closer(self, k=0):
        """1 if the rival is closer to our k-th nearest apple than we are."""
        apple = self.food_list()[k]
        return int(dist(self.rival[0], apple) < dist(self.snake[0], apple))

    def free_space(self, cell):
        """Number of empty cells reachable from `cell` (0 if it is blocked). Small = dead end."""
        if self.blocked(cell):
            return 0
        if self.space_step != self.steps:    # the board changed: forget old answers
            self.space_cache, self.space_step = {}, self.steps
        if cell not in self.space_cache:
            busy = set(self.snake) | set(self.rival)
            seen, todo = {cell}, [cell]
            while todo:                      # flood fill
                x, y = todo.pop()
                for dx, dy in DIRS:
                    nxt = (x + dx, y + dy)
                    if self.inside(nxt) and nxt not in busy and nxt not in seen:
                        seen.add(nxt)
                        todo.append(nxt)
            for c in seen:                   # all these cells share the same answer
                self.space_cache[c] = len(seen)
        return self.space_cache[cell]

    # Output
    def frame(self):
        return {"size": self.size, "snake": list(self.snake), "apples": list(self.apples),
                "rival": list(self.rival), "score": self.score}

    def render(self):
        rows = []
        for y in range(self.size):
            row = ""
            for x in range(self.size):
                c = (x, y)
                row += ("^>v<"[self.direction] + " " if c == self.snake[0] else "o " if c in self.snake else "R " if c == self.rival[0]
                        else "r " if c in self.rival else "* " if c in self.apples else ". ")
            rows.append(row)
        return "\n".join(rows) + "\nscore: %d  step: %d" % (self.score, self.steps)


if __name__ == "__main__":
    # python competitive_snake.py [seed]           watch a random game in the terminal
    # python competitive_snake.py [seed] --play    play yourself: type w (straight), a (left) or d (right) and press Enter.
    #                                              One key = one move (the rival moves too), think as long as you like.
    # Legend: ^ > v < = our head, o = our body, R = rival head, r = rival body, * = apple
    import sys
    import time

    seeds = [arg for arg in sys.argv[1:] if arg.isdigit()]
    game = CompetitiveSnake(seed=int(seeds[0]) if seeds else None)
    keys = {"w": 0, "a": 1, "d": 2}
    died = False
    while not died and game.steps < game.max_steps:
        print("[H[J" + game.render())       # clear the screen and draw the board
        if "--play" in sys.argv:
            key = input("w = straight, a = left, d = right, q = quit > ").strip().lower() or "w"
            if key == "q":
                break
            if key not in keys:
                continue
            action = keys[key]
        else:
            time.sleep(0.1)
            action = random.randint(0, 2)
        ate, died = game.step(action)
    print("game over, apples eaten:", game.score)
