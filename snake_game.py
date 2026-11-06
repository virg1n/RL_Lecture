import random

DIRS = [(0, -1), (1, 0), (0, 1), (-1, 0)]   # up, right, down, left as (dx, dy); y grows downwards
TURN = [0, -1, +1]                          # action 0 = straight, 1 = left, 2 = right


class SnakeGame:
    """One snake, one apple, walls around the field."""

    def __init__(self, size=10, seed=None):
        self.size = size
        self.rng = random.Random(seed)       # same seed = same game
        mid = size // 2
        self.direction = 1                   # looking right
        self.snake = [(mid, mid), (mid - 1, mid), (mid - 2, mid)]   # head first
        self.score = 0
        self.idle = 0                        # moves since the last apple
        self.place_food()

    def place_food(self):
        free = [(x, y) for x in range(self.size) for y in range(self.size) if (x, y) not in self.snake]
        self.food = self.rng.choice(free) if free else None

    def step(self, action):
        """Make one move. Returns (ate, died)."""
        self.direction = (self.direction + TURN[action]) % 4
        new_head = self.next_cell(0)
        if self.is_danger(new_head):
            return False, True
        self.snake.insert(0, new_head)
        self.idle += 1
        ate = new_head == self.food
        if ate:                              # the tail stays, so the snake grows
            self.score += 1
            self.idle = 0
            self.place_food()
            if self.food is None:            # filled the field: the episode is won
                return True, True
        else:
            self.snake.pop()
        return ate, self.idle > 100          # circling for too long also counts as dying

    # What the agent can look at
    def is_danger(self, cell):
        x, y = cell
        return not (0 <= x < self.size and 0 <= y < self.size) or cell in self.snake

    def next_cell(self, turn):
        """The cell in front of the head after a turn (0 = straight, 1 = left, 2 = right)."""
        dx, dy = DIRS[(self.direction + TURN[turn]) % 4]
        return (self.snake[0][0] + dx, self.snake[0][1] + dy)

    def danger_straight(self):
        return int(self.is_danger(self.next_cell(0)))

    def danger_left(self):
        return int(self.is_danger(self.next_cell(1)))

    def danger_right(self):
        return int(self.is_danger(self.next_cell(2)))

    def danger_after(self, actions):
        """1 if a collision occurs within a path of one or two relative actions.

        Example: [0, 1] means straight, then left relative to the NEW heading.
        Predicts walls and the moving body, including growth at the current apple.
        Does not make a real move, spawn food, or consume randomness. Idle timeout
        is not a collision. Restricting paths to two moves avoids needing to know
        the position of a new random apple after eating the current one.
        """
        if not 1 <= len(actions) <= 2 or any(a not in (0, 1, 2) for a in actions):
            raise ValueError("Use one or two actions: 0 = straight, 1 = left, 2 = right")
        body = list(self.snake)
        direction = self.direction
        food = self.food
        for action in actions:
            direction = (direction + TURN[action]) % 4
            dx, dy = DIRS[direction]
            head = (body[0][0] + dx, body[0][1] + dy)
            x, y = head
            if not (0 <= x < self.size and 0 <= y < self.size) or head in body:
                return 1
            body.insert(0, head)
            if head == food:
                food = None
                if len(body) == self.size * self.size:
                    return 0                # the game is won; no second move is needed
            else:
                body.pop()
        return 0

    def food_direction(self):
        """4 bits: is the apple above / right of / below / left of the head?"""
        if self.food is None:               # terminal state after filling the field
            return (0, 0, 0, 0)
        (hx, hy), (fx, fy) = self.snake[0], self.food
        return (int(fy < hy), int(fx > hx), int(fy > hy), int(fx < hx))

    def my_direction(self):
        """4 bits: where the head looks (up, right, down, left)."""
        return tuple(int(self.direction == d) for d in range(4))

    # Output
    def frame(self):
        return {"size": self.size, "snake": list(self.snake), "apples": [self.food] if self.food else [], "rival": [], "score": self.score}

    def render(self):
        rows = []
        for y in range(self.size):
            row = ""
            for x in range(self.size):
                cell = (x, y)
                row += "^>v<"[self.direction] + " " if cell == self.snake[0] else "o " if cell in self.snake else "* " if cell == self.food else ". "
            rows.append(row)
        return "\n".join(rows) + "\nscore: %d" % self.score


if __name__ == "__main__":
    # python snake_game.py [seed]           watch a random game in the terminal
    # python snake_game.py [seed] --play    play yourself: type w (straight), a (left) or d (right) and press Enter.
    #                                       One key = one move, so you can think as long as you like.
    import sys
    import time

    seeds = [arg for arg in sys.argv[1:] if arg.isdigit()]
    game = SnakeGame(seed=int(seeds[0]) if seeds else None)
    keys = {"w": 0, "a": 1, "d": 2}
    died = False
    while not died:
        print("[H[J" + game.render())       # clear the screen and draw the board
        if "--play" in sys.argv:
            key = input("w = straight, a = left, d = right, q = quit > ").strip().lower() or "w"
            if key == "q":
                break
            if key not in keys:
                continue
            action = keys[key]
        else:
            time.sleep(0.15)
            action = random.randint(0, 2)
        ate, died = game.step(action)
    print("game over, apples eaten:", game.score)
