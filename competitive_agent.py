def get_state(game):
    danger = (game.danger_straight(), game.danger_left(), game.danger_right())
    food = game.food_direction()
    direction = game.my_direction()
    state = danger + food + direction
    # Experiment: add ONE extra feature, then train from scratch.
    # state = state + (game.rival_head_near(2),)
    return state
