"""Default player. The host loads Q.json once, then calls play(game, Q) each turn.

Actions: 0 = straight, 1 = left, 2 = right, relative to the head.
The player chooses a move; the host calls game.step(action).
"""


def get_state(game):
    danger = (game.danger_straight(), game.danger_left(), game.danger_right())
    food = game.food_direction()
    direction = game.my_direction()
    return danger + food + direction


# PLAY_POLICY: the notebook copies this function after the student's trained get_state.
def play(game, Q):
    state = get_state(game)
    key = ",".join(str(int(value)) for value in state)
    q = Q.get(key, [0.0, 0.0, 0.0])

    # No preference yet: try a move without an immediate obstacle.
    if q[0] == q[1] == q[2]:
        if game.danger_straight() == 0:
            return 0
        if game.danger_left() == 0:
            return 1
        if game.danger_right() == 0:
            return 2
        return 0

    # Otherwise choose the highest learned value.
    straight = q[0]
    left = q[1]
    right = q[2]
    if straight >= left and straight >= right:
        return 0
    if left >= right:
        return 1
    return 2
