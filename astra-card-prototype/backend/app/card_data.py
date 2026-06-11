import json
from functools import lru_cache
from pathlib import Path


CARD_FILE = Path(__file__).resolve().parents[2] / "shared" / "cards.json"


@lru_cache
def get_cards() -> list[dict]:
    with CARD_FILE.open(encoding="utf-8") as card_file:
        return json.load(card_file)


def get_card(card_id: str) -> dict:
    for card in get_cards():
        if card["id"] == card_id:
            return card
    raise ValueError(f"Unknown card: {card_id}")


def cards_for_faction(faction: str) -> list[dict]:
    return [card for card in get_cards() if card["faction"] == faction]
