from app.card_data import get_card
from app.game_engine import attack, check_winner, create_game, draw_card, end_turn, play_card, resolve_karma


def test_game_creation_has_starting_resources_and_hands():
    game = create_game()
    assert len(game["players"]) == 2
    assert all(player["health"] == 30 for player in game["players"])
    assert all(len(player["hand"]) == 5 for player in game["players"])
    assert game["players"][0]["energy"] == 1


def test_drawing_card_moves_one_from_deck_to_hand():
    game = create_game()
    before = (len(game["players"][0]["deck"]), len(game["players"][0]["hand"]))
    draw_card(game, 0)
    assert len(game["players"][0]["deck"]) == before[0] - 1
    assert len(game["players"][0]["hand"]) == before[1] + 1


def test_playing_card_reduces_energy():
    game = create_game()
    player = game["players"][0]
    player["energy"] = 10
    player["hand"] = ["ob-w01"]
    play_card(game, 0, 0)
    assert player["energy"] == 10 - get_card("ob-w01")["cost"]
    assert len(player["board"]) == 1


def test_attack_reduces_health_and_unbalanced_takes_extra():
    game = create_game()
    attacker = game["players"][0]
    enemy = game["players"][1]
    attacker["board"] = [{"name": "Test", "attack": 3, "defense": 3, "ready": True}]
    enemy["dharma"] = 0
    attack(game, 0, 0)
    assert enemy["health"] == 26


def test_karma_debt_triggers_after_delay():
    game = create_game()
    player = game["players"][0]
    player["karma_debt"] = 3
    player["karma_timer"] = 1
    resolve_karma(game, 0)
    assert player["health"] == 27
    assert player["karma_debt"] == 0


def test_winner_detection():
    game = create_game()
    game["players"][1]["health"] = 0
    assert check_winner(game) == 0
    assert game["phase"] == "finished"


def test_oath_reward_arrives_on_players_next_turn():
    game = create_game()
    player = game["players"][0]
    player["energy"] = 10
    player["hand"] = ["ob-o01"]
    play_card(game, 0, 0)
    end_turn(game, 0)
    assert player["dharma"] == 5
    end_turn(game, 1)
    assert player["dharma"] == 7
