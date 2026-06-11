from fastapi import WebSocket

from .game_engine import public_state
from .room_manager import Room


async def broadcast(room: Room) -> None:
    stale: list[tuple[int, WebSocket]] = []
    for player_index, sockets in room.sockets.items():
        payload = {
            "type": "state",
            "room_id": room.room_id,
            "player_index": player_index,
            "state": public_state(room.game, player_index),
        }
        for socket in sockets:
            try:
                await socket.send_json(payload)
            except RuntimeError:
                stale.append((player_index, socket))
    for player_index, socket in stale:
        room.sockets[player_index].discard(socket)
