import json
import random
import shutil

from competitive_snake import CompetitiveSnake


def state_key(state):
    """Turn the state tuple into a text key, e.g. (0, 1, 1) -> "0,1,1". (JSON needs text keys.)"""
    return ",".join(str(int(value)) for value in state)


def q_values(Q, key):
    """The 3 Q-values [straight, left, right] of a state (a new state starts with zeros)."""
    if key not in Q:
        Q[key] = [0.0, 0.0, 0.0]
    return Q[key]


def train(get_state, REWARD_FOOD=10, REWARD_DEATH=-10, REWARD_STEP=0, REWARD_CLOSER=0,
          ALPHA=0.1, GAMMA=0.9, EPSILON_DECAY=0.995, EPISODES=3000,
          learn=None, seed=1):
    """Train from scratch. Optional learn(q, action, reward, best_next) changes q in place.

    With a custom learn function, its own ALPHA/GAMMA are used. Without one,
    the arguments ALPHA/GAMMA control the standard Q-learning update.
    A fixed seed makes repeated experiments comparable.
    """
    Q = {}
    rng = random.Random(seed)
    epsilon = 1.0
    recent = []                                   # apples eaten in the last training games

    for episode in range(1, EPISODES + 1):
        game = CompetitiveSnake(seed=rng.randrange(2**32))
        state = state_key(get_state(game))
        done = False

        while not done:
            # 1. choose an action: sometimes explore, otherwise take the best known one
            q = q_values(Q, state)
            if rng.random() < epsilon:
                action = rng.randint(0, 2)
            else:
                best = max(q)
                action = rng.choice([a for a in range(3) if q[a] == best])

            # 2. make the move
            distance_before = game.food_distance()
            ate, died = game.step(action)

            # 3. reward for this move
            reward = REWARD_STEP
            if ate:
                reward += REWARD_FOOD
            if died:
                reward += REWARD_DEATH
            if not ate and not died:              # did we get closer to the nearest apple?
                if game.food_distance() < distance_before:
                    reward += REWARD_CLOSER
                else:
                    reward -= REWARD_CLOSER

            # 4. learn: move Q[state][action] towards  reward + GAMMA * (best future value)
            done = died or game.steps >= game.max_steps
            if done:
                next_state = None
                best_next = 0
            else:
                next_state = state_key(get_state(game))
                best_next = max(q_values(Q, next_state))
            if learn is None:
                target = reward + GAMMA * best_next
                q[action] += ALPHA * (target - q[action])
            else:
                learn(q, action, reward, best_next)

            state = next_state

        epsilon = max(0.01, epsilon * EPSILON_DECAY)
        recent.append(game.score)
        if episode % 500 == 0:
            print("episode %d / %d   apples per game (last 100): %.1f   states seen: %d"
                  % (episode, EPISODES, sum(recent[-100:]) / 100, len(Q)))
    return Q


def pick_action(game, Q, get_state):
    """The policy that is judged: argmax of Q. For unknown states take any move that is not deadly."""
    q = Q.get(state_key(get_state(game)))
    if q is None or max(q) == min(q):
        dangers = [game.danger_straight(), game.danger_left(), game.danger_right()]
        return dangers.index(0) if 0 in dangers else 0
    return q.index(max(q))


def play_game(Q, get_state, seed):
    """One complete game with the learned Q-table. Returns the number of apples eaten."""
    game = CompetitiveSnake(seed=seed)
    while game.steps < game.max_steps:
        ate, died = game.step(pick_action(game, Q, get_state))
        if died:
            break
    return game.score


def evaluate(Q, get_state, seeds=range(1, 31)):
    """Average score over several games (the server does the same with 200 secret seeds)."""
    scores = [play_game(Q, get_state, seed) for seed in seeds]
    return sum(scores) / len(scores)


def save_submission(Q, folder="."):
    """Write qtable.json (and a copy of agent.py into `folder`). Upload both files to the site."""
    with open(folder + "/qtable.json", "w") as f:
        json.dump(Q, f)
    if folder != ".":
        shutil.copy("agent.py", folder + "/agent.py")
    print("saved %d states to %s/qtable.json" % (len(Q), folder))
