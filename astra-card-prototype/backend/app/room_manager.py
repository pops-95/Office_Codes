import asyncio
import secrets
from dataclasses import dataclass, field

from .game_engine import create_game


@dataclass
class Room:
    room_id: str
    game: dict
    player_tokens: list[str | None]
    sockets: dict[int, set] = field(default_factory=lambda: {0: set(), 1: set()})
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class RoomManager:
    def __init__(self) -> None:
        self.rooms: dict[str, Room] = {}

    def create(self, player_name: str) -> tuple[Room, str]:
        room_id = secrets.token_hex(3).upper()
        while room_id in self.rooms:
            room_id = secrets.token_hex(3).upper()
        token = secrets.token_urlsafe(18)
        game = create_game([player_name, "Awaiting challenger"])
        room = Room(room_id, game, [token, None])
        self.rooms[room_id] = room
        return room, token

    def get(self, room_id: str) -> Room:
        room = self.rooms.get(room_id.upper())
        if room is None:
            raise KeyError("Room not found")
        return room

    def join(self, room: Room, player_name: str, token: str | None) -> tuple[int, str]:
        if token is not None and token in room.player_tokens:
            return room.player_tokens.index(token), token or ""
        if room.player_tokens[1] is not None:
            raise ValueError("Room is full")
        new_token = secrets.token_urlsafe(18)
        room.player_tokens[1] = new_token
        room.game["players"][1]["name"] = player_name
        room.game["log"].append(f"{player_name} joins the Night Court.")
        return 1, new_token


room_manager = RoomManager()
