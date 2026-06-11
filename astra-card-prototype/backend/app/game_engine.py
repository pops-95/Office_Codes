import copy
import random
import uuid
from typing import Any

from .card_data import cards_for_faction, get_card

MAX_BOARD = 5


def _player(name: str, faction: str) -> dict[str, Any]:
    deck = [card["id"] for card in cards_for_faction(faction)] * 2
    random.shuffle(deck)
    return {
        "id": uuid.uuid4().hex,
        "name": name,
        "faction": faction,
        "health": 30,
        "dharma": 5,
        "karma_debt": 0,
        "karma_timer": 0,
        "energy": 0,
        "max_energy": 0,
        "deck": deck,
        "hand": [],
        "board": [],
        "realm": None,
        "oaths": [],
        "oath_rewards": [],
        "attacked_this_turn": False,
        "cards_played_this_turn": 0,
    }


def create_game(player_names: list[str] | None = None) -> dict[str, Any]:
    names = player_names or ["Player One", "Player Two"]
    game = {
        "id": uuid.uuid4().hex,
        "players": [_player(names[0], "Oathbound"), _player(names[1], "Night Court")],
        "current_player": 0,
        "turn": 1,
        "phase": "playing",
        "winner": None,
        "log": ["The astral gate opens. Player One begins."],
    }
    for player in game["players"]:
        for _ in range(5):
            draw_card(game, game["players"].index(player), log=False)
    start_turn(game, 0)
    return game


def public_state(game: dict[str, Any], viewer_index: int | None = None) -> dict[str, Any]:
    state = copy.deepcopy(game)
    for index, player in enumerate(state["players"]):
        player["deck_count"] = len(player.pop("deck"))
        if viewer_index is None or index != viewer_index:
            player["hand_count"] = len(player["hand"])
            player["hand"] = []
    return state


def draw_card(game: dict[str, Any], player_index: int, log: bool = True) -> str | None:
    player = game["players"][player_index]
    if not player["deck"]:
        player["health"] -= 1
        if log:
            game["log"].append(f"{player['name']} takes 1 fatigue damage.")
        check_winner(game)
        return None
    card_id = player["deck"].pop()
    player["hand"].append(card_id)
    if log:
        game["log"].append(f"{player['name']} draws a card.")
    return card_id


def _add_karma(player: dict[str, Any], amount: int) -> None:
    player["karma_debt"] += amount
    if player["karma_timer"] == 0:
        player["karma_timer"] = 2


def _damage(game: dict[str, Any], player_index: int, amount: int, attack: bool = False) -> int:
    target = game["players"][player_index]
    actual = amount + (1 if attack and target["dharma"] <= 0 else 0)
    target["health"] -= actual
    check_winner(game)
    return actual


def _buff_board(player: dict[str, Any], attack: int = 0, defense: int = 0) -> None:
    for warrior in player["board"]:
        warrior["attack"] = max(0, warrior["attack"] + attack)
        warrior["defense"] += defense


def apply_card_effect(game: dict[str, Any], player_index: int, card: dict) -> None:
    player = game["players"][player_index]
    enemy = game["players"][1 - player_index]
    key = card["effect_key"]
    if key == "none":
        return
    if key.startswith("gain_dharma_"):
        player["dharma"] += int(key.rsplit("_", 1)[1])
    elif key == "restore_dharma_if_low" and player["dharma"] < 5:
        player["dharma"] += 1
    elif key.startswith("heal_"):
        player["health"] = min(30, player["health"] + int(key.rsplit("_", 1)[1]))
    elif key.startswith("damage_enemy_"):
        _damage(game, 1 - player_index, int(key.rsplit("_", 1)[1]))
    elif key == "fortify_allies_1":
        _buff_board(player, defense=1)
    elif key == "draw_1":
        draw_card(game, player_index)
    elif key == "promise_unbroken":
        player["health"] = min(30, player["health"] + 3)
        player["dharma"] += 2
    elif key.startswith("self_karma_"):
        _add_karma(player, int(key.rsplit("_", 1)[1]))
    elif key == "enemy_karma_1":
        _add_karma(enemy, 1)
    elif key.startswith("drain_dharma_"):
        enemy["dharma"] = max(0, enemy["dharma"] - int(key.rsplit("_", 1)[1]))
    elif key == "weaken_all_1":
        _buff_board(enemy, attack=-1)
    elif key == "last_echoes":
        _damage(game, 1 - player_index, 3)
        _add_karma(enemy, 1)
    elif key == "power_strike_4":
        _damage(game, 1 - player_index, 4)
        player["dharma"] = max(0, player["dharma"] - 1)
    elif key == "rally_allies_1":
        _buff_board(player, attack=1, defense=1)
    elif key == "risky_damage_2":
        _damage(game, 1 - player_index, 2)
        _add_karma(player, 1)
    elif key == "debtcoil":
        _damage(game, 1 - player_index, 3)
        _add_karma(enemy, 1)
    elif key == "eclipse_cannon":
        _damage(game, 1 - player_index, 6)
        player["dharma"] = max(0, player["dharma"] - 1)
        _add_karma(player, 1)
    elif key == "rally_attack_2":
        _buff_board(player, attack=2)
    elif key == "oath_still_waters":
        player["oaths"].append({"key": key, "played_turn": game["turn"]})
    elif key == "oath_open_hand":
        player["oaths"].append({"key": key, "played_turn": game["turn"]})
    elif key == "oath_velvet_knives":
        player["oaths"].append({"key": key, "played_turn": game["turn"]})
    elif key == "oath_shared_dawn":
        player["dharma"] += 1
        _buff_board(player, defense=1)
    elif key == "oath_borrowed_hours":
        player["energy"] += 2
        _add_karma(player, 1)
    elif key == "oath_hollow_crown":
        _damage(game, 1 - player_index, 3)
        enemy["dharma"] = max(0, enemy["dharma"] - 1)
    elif key == "radiant_reckoning":
        _damage(game, 1 - player_index, 2)
        player["karma_debt"] = max(0, player["karma_debt"] - 1)
        if player["karma_debt"] == 0:
            player["karma_timer"] = 0
    elif key == "discard_enemy_1" and enemy["hand"]:
        enemy["hand"].pop(random.randrange(len(enemy["hand"])))
    elif key == "karma_burst":
        _damage(game, 1 - player_index, max(2, enemy["karma_debt"]))


def play_card(game: dict[str, Any], player_index: int, card_index: int) -> dict[str, Any]:
    _assert_turn(game, player_index)
    player = game["players"][player_index]
    if card_index < 0 or card_index >= len(player["hand"]):
        raise ValueError("Invalid card index")
    card = get_card(player["hand"][card_index])
    if card["cost"] > player["energy"]:
        raise ValueError("Not enough energy")
    if card["type"] == "Warrior" and len(player["board"]) >= MAX_BOARD:
        raise ValueError("The battlefield is full")
    player["energy"] -= card["cost"]
    player["hand"].pop(card_index)
    player["cards_played_this_turn"] += 1
    if card["type"] == "Warrior":
        attack_bonus = 1 if player["realm"] == "realm_bazaar" else 0
        defense_bonus = 1 if player["realm"] == "realm_citadel" else 0
        player["board"].append({
            "instance_id": uuid.uuid4().hex[:8],
            "card_id": card["id"],
            "name": card["name"],
            "attack": card["attack"] + attack_bonus,
            "defense": card["defense"] + defense_bonus,
            "ready": False,
        })
    elif card["type"] == "Realm":
        player["realm"] = card["effect_key"]
    apply_card_effect(game, player_index, card)
    game["log"].append(f"{player['name']} plays {card['name']}.")
    check_winner(game)
    return game


def attack(
    game: dict[str, Any],
    player_index: int,
    attacker_index: int,
    target_index: int | None = None,
) -> dict[str, Any]:
    _assert_turn(game, player_index)
    player = game["players"][player_index]
    enemy = game["players"][1 - player_index]
    if attacker_index < 0 or attacker_index >= len(player["board"]):
        raise ValueError("Invalid attacker")
    attacker = player["board"][attacker_index]
    if not attacker["ready"]:
        raise ValueError("That warrior cannot attack yet")
    attacker["ready"] = False
    player["attacked_this_turn"] = True
    if target_index is None:
        dealt = _damage(game, 1 - player_index, attacker["attack"], attack=True)
        game["log"].append(f"{attacker['name']} strikes {enemy['name']} for {dealt}.")
    else:
        if target_index < 0 or target_index >= len(enemy["board"]):
            raise ValueError("Invalid target")
        defender = enemy["board"][target_index]
        defender["defense"] -= attacker["attack"]
        attacker["defense"] -= defender["attack"]
        game["log"].append(f"{attacker['name']} clashes with {defender['name']}.")
        enemy["board"] = [unit for unit in enemy["board"] if unit["defense"] > 0]
        player["board"] = [unit for unit in player["board"] if unit["defense"] > 0]
    check_winner(game)
    return game


def _resolve_oaths(game: dict[str, Any], player_index: int) -> None:
    player = game["players"][player_index]
    for oath in player["oaths"]:
        success = False
        if oath["key"] == "oath_still_waters":
            success = not player["attacked_this_turn"]
        elif oath["key"] == "oath_open_hand":
            success = player["cards_played_this_turn"] == 1
        elif oath["key"] == "oath_velvet_knives":
            success = player["attacked_this_turn"]
        if success:
            player["oath_rewards"].append(oath["key"])
        game["log"].append(
            f"{player['name']}'s oath {'is fulfilled; its reward awaits' if success else 'fades unfulfilled'}."
        )
    player["oaths"] = []


def resolve_karma(game: dict[str, Any], player_index: int) -> None:
    player = game["players"][player_index]
    if player["karma_debt"] <= 0:
        player["karma_timer"] = 0
        return
    player["karma_timer"] -= 1
    if player["karma_timer"] <= 0:
        debt = player["karma_debt"]
        player["health"] -= debt
        player["karma_debt"] = 0
        player["karma_timer"] = 0
        game["log"].append(f"Karma comes due: {player['name']} takes {debt} damage.")
        check_winner(game)


def start_turn(game: dict[str, Any], player_index: int) -> None:
    player = game["players"][player_index]
    for reward in player["oath_rewards"]:
        if reward == "oath_still_waters":
            player["dharma"] += 2
        elif reward == "oath_open_hand":
            player["health"] = min(30, player["health"] + 4)
        elif reward == "oath_velvet_knives":
            draw_card(game, player_index)
            _add_karma(player, 1)
        game["log"].append(f"{player['name']} receives a fulfilled oath's reward.")
    player["oath_rewards"] = []
    player["max_energy"] = min(10, player["max_energy"] + 1)
    player["energy"] = player["max_energy"]
    player["attacked_this_turn"] = False
    player["cards_played_this_turn"] = 0
    for warrior in player["board"]:
        warrior["ready"] = True
    if player["realm"] == "realm_archive":
        player["dharma"] += 1
    elif player["realm"] == "realm_palace":
        _damage(game, 1 - player_index, 1)
    if game["turn"] > 1:
        draw_card(game, player_index)
    game["log"].append(f"{player['name']} begins turn {game['turn']}.")


def end_turn(game: dict[str, Any], player_index: int) -> dict[str, Any]:
    _assert_turn(game, player_index)
    _resolve_oaths(game, player_index)
    resolve_karma(game, player_index)
    if game["winner"] is not None:
        return game
    game["current_player"] = 1 - player_index
    game["turn"] += 1
    start_turn(game, game["current_player"])
    return game


def check_winner(game: dict[str, Any]) -> int | None:
    dead = [index for index, player in enumerate(game["players"]) if player["health"] <= 0]
    if dead:
        game["winner"] = 1 - dead[0]
        game["phase"] = "finished"
        game["log"].append(f"{game['players'][game['winner']]['name']} wins the match.")
    return game["winner"]


def _assert_turn(game: dict[str, Any], player_index: int) -> None:
    if game["phase"] != "playing":
        raise ValueError("The match is over")
    if game["current_player"] != player_index:
        raise ValueError("It is not your turn")
