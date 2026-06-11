from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .card_data import get_cards
from .game_engine import attack, end_turn, play_card, public_state
from .models import GameAction, RoomCreate
from .room_manager import room_manager
from .websocket_manager import broadcast

app = FastAPI(title="Astra: Oath & Karma API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "rooms": len(room_manager.rooms)}


@app.get("/cards")
def cards() -> list[dict]:
    return get_cards()


@app.post("/rooms")
def create_room(payload: RoomCreate) -> dict:
    room, token = room_manager.create(payload.player_name)
    return {
        "room_id": room.room_id,
        "player_id": token,
        "player_index": 0,
        "state": public_state(room.game, 0),
    }


@app.get("/rooms/{room_id}")
def get_room(room_id: str) -> dict:
    try:
        room = room_manager.get(room_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "room_id": room.room_id,
        "player_count": sum(token is not None for token in room.player_tokens),
        "status": room.game["phase"],
        "state": public_state(room.game),
    }


@app.websocket("/ws/rooms/{room_id}")
async def room_socket(websocket: WebSocket, room_id: str) -> None:
    try:
        room = room_manager.get(room_id)
    except KeyError:
        await websocket.close(code=4404, reason="Room not found")
        return
    await websocket.accept()
    player_index: int | None = None
    try:
        first = GameAction.model_validate(await websocket.receive_json())
        if first.type != "join":
            await websocket.close(code=4400, reason="Join action required")
            return
        try:
            player_index, token = room_manager.join(
                room, first.player_name or "Challenger", first.player_id
            )
        except ValueError as exc:
            await websocket.close(code=4403, reason=str(exc))
            return
        room.sockets[player_index].add(websocket)
        await websocket.send_json({"type": "joined", "player_id": token, "player_index": player_index})
        await broadcast(room)
        while True:
            action = GameAction.model_validate(await websocket.receive_json())
            if action.player_id != room.player_tokens[player_index]:
                await websocket.send_json({"type": "error", "message": "Invalid player token"})
                continue
            try:
                async with room.lock:
                    if action.type == "play_card":
                        play_card(room.game, player_index, action.card_index or 0)
                    elif action.type == "attack":
                        attack(
                            room.game,
                            player_index,
                            action.attacker_index or 0,
                            action.target_index,
                        )
                    elif action.type == "end_turn":
                        end_turn(room.game, player_index)
                    else:
                        raise ValueError("Unsupported action")
                await broadcast(room)
            except ValueError as exc:
                await websocket.send_json({"type": "error", "message": str(exc)})
    except WebSocketDisconnect:
        pass
    finally:
        if player_index is not None:
            room.sockets[player_index].discard(websocket)
