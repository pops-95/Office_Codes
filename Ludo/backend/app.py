import ipaddress
import os
import random
import re
import secrets
import threading
import time
from dataclasses import dataclass, field

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room


TURN_SECONDS = 15
DICE_REVEAL_SECONDS = 2
COLORS = ["red", "green", "yellow", "blue"]
START_OFFSETS = {"red": 0, "green": 13, "yellow": 26, "blue": 39}
SAFE_SPACES = {0, 8, 13, 21, 26, 34, 39, 47}

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", secrets.token_hex(24))
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

rooms = {}
sid_index = {}
rooms_lock = threading.RLock()


@dataclass
class Player:
    id: str
    name: str
    color: str
    sid: str
    connected: bool = True
    tokens: list = field(default_factory=lambda: [-1, -1, -1, -1])

    def public(self):
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color,
            "connected": self.connected,
            "tokens": self.tokens,
        }


@dataclass
class Room:
    code: str
    network: str
    host_id: str
    max_players: int = 4
    players: list = field(default_factory=list)
    started: bool = False
    current_turn: int = 0
    dice: int | None = None
    dice_rolled_at: float | None = None
    dice_available_at: float | None = None
    roll_nonce: int = 0
    consecutive_sixes: int = 0
    winner_id: str | None = None
    turn_deadline: float | None = None
    timer_version: int = 0
    messages: list = field(default_factory=list)

    def player(self, player_id):
        return next((p for p in self.players if p.id == player_id), None)

    def public(self):
        return {
            "code": self.code,
            "hostId": self.host_id,
            "maxPlayers": self.max_players,
            "players": [p.public() for p in self.players],
            "started": self.started,
            "currentPlayerId": (
                self.players[self.current_turn].id
                if self.started and self.players
                else None
            ),
            "dice": self.dice,
            "diceRolledAt": self.dice_rolled_at,
            "diceAvailableAt": self.dice_available_at,
            "rollNonce": self.roll_nonce,
            "consecutiveSixes": self.consecutive_sixes,
            "winnerId": self.winner_id,
            "turnDeadline": self.turn_deadline,
            "turnSeconds": TURN_SECONDS,
            "messages": self.messages[-100:],
        }


def client_network():
    raw = request.remote_addr or "127.0.0.1"
    try:
        address = ipaddress.ip_address(raw)
        prefix = 24 if address.version == 4 else 64
        return str(ipaddress.ip_network(f"{address}/{prefix}", strict=False))
    except ValueError:
        return raw


def clean_name(value):
    name = re.sub(r"\s+", " ", str(value or "")).strip()
    return name[:24] or "Player"


def make_code():
    while True:
        code = f"{random.randint(0, 9999):04d}"
        if code not in rooms:
            return code


def current_player(room):
    if not room.players:
        return None
    return room.players[room.current_turn]


def destination_progress(progress, dice):
    return 0 if progress == -1 and dice == 6 else progress + dice


def is_protected_block(room, moving_player, landing):
    if landing is None or landing in SAFE_SPACES:
        return False
    for opponent in room.players:
        if opponent.id == moving_player.id:
            continue
        occupants = sum(
            board_position(opponent, progress) == landing
            for progress in opponent.tokens
        )
        if occupants >= 2:
            return True
    return False


def legal_tokens(room, player, dice):
    legal = []
    for index, progress in enumerate(player.tokens):
        if progress == 57:
            continue
        can_leave_home = progress == -1 and dice == 6
        can_advance = progress >= 0 and progress + dice <= 57
        if not (can_leave_home or can_advance):
            continue
        destination = destination_progress(progress, dice)
        landing = board_position(player, destination)
        if not is_protected_block(room, player, landing):
            legal.append(index)
    return legal


def board_position(player, progress):
    if 0 <= progress <= 51:
        return (START_OFFSETS[player.color] + progress) % 52
    return None


def reset_turn_timer(room):
    room.timer_version += 1
    version = room.timer_version
    room.turn_deadline = time.time() + TURN_SECONDS
    socketio.start_background_task(turn_timeout, room.code, version)


def roll_for_room(room):
    maximum = 5 if room.consecutive_sixes >= 2 else 6
    room.dice = random.randint(1, maximum)
    room.consecutive_sixes = room.consecutive_sixes + 1 if room.dice == 6 else 0
    room.dice_rolled_at = time.time()
    room.dice_available_at = room.dice_rolled_at + DICE_REVEAL_SECONDS
    room.roll_nonce += 1
    return room.roll_nonce


def finish_empty_roll(code, roll_nonce, automatic=False, delay=None):
    socketio.sleep((DICE_REVEAL_SECONDS if delay is None else delay) + 0.05)
    with rooms_lock:
        room = rooms.get(code)
        if (
            not room
            or not room.started
            or room.winner_id
            or room.roll_nonce != roll_nonce
            or room.dice is None
        ):
            return
        player = current_player(room)
        legal = legal_tokens(room, player, room.dice)
        if automatic and legal:
            move_token(room, player, legal[0], automatic=True)
        elif not legal:
            announce(room, f"{player.name} had no legal move.")
            finish_turn(room, extra_turn=False)
        else:
            return
        broadcast_room(room)


def turn_timeout(code, version):
    socketio.sleep(TURN_SECONDS + 0.15)
    with rooms_lock:
        room = rooms.get(code)
        if (
            not room
            or not room.started
            or room.winner_id
            or room.timer_version != version
            or time.time() < (room.turn_deadline or 0)
        ):
            return
        player = current_player(room)
        if room.dice is None:
            roll_nonce = roll_for_room(room)
            broadcast_room(room)
            socketio.start_background_task(
                finish_empty_roll, room.code, roll_nonce, True
            )
            return
        if time.time() < (room.dice_available_at or 0):
            socketio.start_background_task(
                finish_empty_roll,
                room.code,
                room.roll_nonce,
                True,
                max(0, room.dice_available_at - time.time()),
            )
            return
        legal = legal_tokens(room, player, room.dice)
        if legal:
            move_token(room, player, legal[0], automatic=True)
        else:
            announce(room, f"{player.name} had no legal move.")
            finish_turn(room, extra_turn=False)
        broadcast_room(room)


def announce(room, text):
    room.messages.append(
        {
            "id": secrets.token_hex(6),
            "senderId": "system",
            "senderName": "Game",
            "text": text,
            "mentions": [],
            "timestamp": time.time(),
            "system": True,
        }
    )


def finish_turn(room, extra_turn):
    room.dice = None
    room.dice_rolled_at = None
    room.dice_available_at = None
    if not extra_turn:
        room.consecutive_sixes = 0
        room.current_turn = (room.current_turn + 1) % len(room.players)
    reset_turn_timer(room)


def move_token(room, player, token_index, automatic=False):
    dice = room.dice
    old_progress = player.tokens[token_index]
    new_progress = 0 if old_progress == -1 else old_progress + dice
    player.tokens[token_index] = new_progress

    captured = False
    landing = board_position(player, new_progress)
    if landing is not None and landing not in SAFE_SPACES:
        for opponent in room.players:
            if opponent.id == player.id:
                continue
            occupants = [
                index
                for index, progress in enumerate(opponent.tokens)
                if board_position(opponent, progress) == landing
            ]
            if len(occupants) == 1:
                opponent.tokens[occupants[0]] = -1
                captured = True

    prefix = "Auto-moved" if automatic else "Moved"
    announce(room, f"{prefix} {player.name}'s token {token_index + 1}.")

    if all(progress == 57 for progress in player.tokens):
        room.winner_id = player.id
        room.turn_deadline = None
        room.timer_version += 1
        announce(room, f"{player.name} wins the game!")
        return

    finish_turn(room, extra_turn=(dice == 6 or captured))


def broadcast_room(room):
    socketio.emit("room_state", room.public(), to=room.code)


def require_room(data):
    code = str(data.get("code", "")).upper()
    player_id = str(data.get("playerId", ""))
    room = rooms.get(code)
    player = room.player(player_id) if room else None
    if not room or not player:
        emit("game_error", {"message": "Room or player not found."})
        return None, None
    return room, player


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "rooms": len(rooms)})


@socketio.on("create_room")
def create_room(data):
    with rooms_lock:
        code = make_code()
        player_id = str(data.get("playerId") or secrets.token_hex(12))
        try:
            max_players = int(data.get("maxPlayers", 4))
        except (TypeError, ValueError):
            max_players = 4
        max_players = max(2, min(4, max_players))
        player = Player(player_id, clean_name(data.get("name")), COLORS[0], request.sid)
        room = Room(
            code=code,
            network=client_network(),
            host_id=player_id,
            max_players=max_players,
            players=[player],
        )
        rooms[code] = room
        sid_index[request.sid] = (code, player_id)
        join_room(code)
        emit("room_joined", {"playerId": player_id, "room": room.public()})


@socketio.on("join_room")
def join_existing_room(data):
    code = str(data.get("code", "")).strip()
    with rooms_lock:
        if not re.fullmatch(r"\d{4}", code):
            emit("game_error", {"message": "Invite code must contain exactly 4 digits."})
            return
        room = rooms.get(code)
        if not room:
            emit("game_error", {"message": "Invite code not found."})
            return
        if room.network != client_network():
            emit("game_error", {"message": "This invite only works on the host's local network."})
            return

        player_id = str(data.get("playerId") or secrets.token_hex(12))
        existing = room.player(player_id)
        if existing:
            existing.sid = request.sid
            existing.connected = True
            existing.name = clean_name(data.get("name") or existing.name)
            player = existing
        else:
            if room.started:
                emit("game_error", {"message": "This game has already started."})
                return
            if len(room.players) >= room.max_players:
                emit("game_error", {"message": "This room is full."})
                return
            player = Player(
                player_id,
                clean_name(data.get("name")),
                COLORS[len(room.players)],
                request.sid,
            )
            room.players.append(player)

        sid_index[request.sid] = (code, player.id)
        join_room(code)
        emit("room_joined", {"playerId": player.id, "room": room.public()})
        announce(room, f"{player.name} joined the room.")
        broadcast_room(room)


@socketio.on("rename")
def rename(data):
    with rooms_lock:
        room, player = require_room(data)
        if not room:
            return
        old_name = player.name
        player.name = clean_name(data.get("name"))
        announce(room, f"{old_name} is now {player.name}.")
        broadcast_room(room)


@socketio.on("start_game")
def start_game(data):
    with rooms_lock:
        room, player = require_room(data)
        if not room:
            return
        if player.id != room.host_id:
            emit("game_error", {"message": "Only the host can start the game."})
            return
        if len(room.players) != room.max_players:
            emit(
                "game_error",
                {"message": f"Waiting for {room.max_players - len(room.players)} more player(s)."},
            )
            return
        room.started = True
        room.current_turn = 0
        room.dice = None
        room.dice_rolled_at = None
        room.dice_available_at = None
        room.consecutive_sixes = 0
        announce(room, "The game has started.")
        reset_turn_timer(room)
        broadcast_room(room)


@socketio.on("roll_dice")
def roll_dice(data):
    with rooms_lock:
        room, player = require_room(data)
        if not room or not room.started or room.winner_id:
            return
        if current_player(room).id != player.id or room.dice is not None:
            emit("game_error", {"message": "It is not your roll."})
            return
        roll_nonce = roll_for_room(room)
        broadcast_room(room)
        if not legal_tokens(room, player, room.dice):
            socketio.start_background_task(
                finish_empty_roll, room.code, roll_nonce
            )


@socketio.on("move_token")
def handle_move(data):
    with rooms_lock:
        room, player = require_room(data)
        if not room or not room.started or room.winner_id:
            return
        if current_player(room).id != player.id or room.dice is None:
            emit("game_error", {"message": "It is not your move."})
            return
        if time.time() < (room.dice_available_at or 0):
            emit("game_error", {"message": "Wait for the dice to finish rolling."})
            return
        try:
            token_index = int(data.get("tokenIndex"))
        except (TypeError, ValueError):
            token_index = -1
        if token_index not in legal_tokens(room, player, room.dice):
            emit("game_error", {"message": "That token cannot move with this roll."})
            return
        move_token(room, player, token_index)
        broadcast_room(room)


@socketio.on("chat_message")
def chat_message(data):
    with rooms_lock:
        room, player = require_room(data)
        if not room:
            return
        text = str(data.get("text", "")).strip()[:500]
        if not text:
            return
        mentions = [
            candidate.id
            for candidate in room.players
            if f"@{candidate.name}".lower() in text.lower()
        ]
        message = {
            "id": secrets.token_hex(6),
            "senderId": player.id,
            "senderName": player.name,
            "text": text,
            "mentions": mentions,
            "timestamp": time.time(),
            "system": False,
        }
        room.messages.append(message)
        socketio.emit("chat_message", message, to=room.code)


@socketio.on("disconnect")
def disconnect():
    with rooms_lock:
        identity = sid_index.pop(request.sid, None)
        if not identity:
            return
        code, player_id = identity
        room = rooms.get(code)
        player = room.player(player_id) if room else None
        if player:
            player.connected = False
            broadcast_room(room)


if __name__ == "__main__":
    socketio.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "5000")),
        debug=os.environ.get("FLASK_DEBUG", "1") == "1",
        allow_unsafe_werkzeug=True,
    )
