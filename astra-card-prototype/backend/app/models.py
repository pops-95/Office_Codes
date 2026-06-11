from typing import Any, Literal

from pydantic import BaseModel, Field


class RoomCreate(BaseModel):
    player_name: str = Field(default="Player One", min_length=1, max_length=30)


class GameAction(BaseModel):
    type: Literal["join", "play_card", "attack", "end_turn", "restart"]
    player_id: str | None = None
    player_name: str | None = None
    card_index: int | None = None
    attacker_index: int | None = None
    target_index: int | None = None


class RoomSummary(BaseModel):
    room_id: str
    player_count: int
    status: str
    state: dict[str, Any]
