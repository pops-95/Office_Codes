# Astra: Oath & Karma

A complete browser prototype for an original 1v1 collectible strategy card game. It combines an Indian mythology-inspired modern fantasy setting with original factions, characters, realms, and lore. No direct mythological characters or copyrighted artwork are used.

## What Is Included

- Polished responsive landing page
- Searchable 40-card archive
- Local match against a simple AI
- Authoritative FastAPI multiplayer rooms over WebSockets
- Two factions: defensive Oathbound and high-risk Night Court
- Warriors, Weapons, Oaths, Curses, and Realms
- Working Dharma, delayed Karma Debt, and three conditional Oath effects
- Server engine tests and a production frontend build

## Tech Stack

**Frontend:** React 19, TypeScript, Vite, Tailwind CSS, Zustand, Framer Motion, React Router, and Lucide React.

**Backend:** Python, FastAPI, Pydantic, Uvicorn, in-memory room state, native WebSockets, and Pytest.

SQLite is intentionally omitted because the prototype only stores active room state in memory. A database becomes useful when accounts, deck building, match history, or reconnect persistence are added.

## Folder Structure

```text
astra-card-prototype/
├── shared/cards.json        # Canonical 40-card catalog
├── frontend/
│   ├── src/components/      # Cards, board, and navigation
│   ├── src/game/            # Local TypeScript rules engine
│   ├── src/routes/          # Required application screens
│   └── src/store/           # Zustand demo state
├── backend/
│   ├── app/                 # API, rules engine, and room management
│   └── tests/               # Backend engine tests
└── docker-compose.yml
```

## Run Locally

### Backend

```bash
cd astra-card-prototype/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API documentation is available at `http://localhost:8000/docs`.

### Frontend

In a second terminal:

```bash
cd astra-card-prototype/frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

### Docker Compose

From `astra-card-prototype`:

```bash
docker compose up --build
```

The frontend runs at `http://localhost:5173` and FastAPI at `http://localhost:8000`.

## API

- `GET /health`
- `GET /cards`
- `POST /rooms` with `{ "player_name": "Name" }`
- `GET /rooms/{room_id}`
- `WS /ws/rooms/{room_id}`

## Rules

Each player begins with 30 health, 5 Dharma, no Karma Debt, and five cards. Energy rises by one on each of that player's turns to a maximum of ten. Spend energy to play cards, attack with ready warriors, then end the turn.

- **Warriors** enter the battlefield and can attack from their next turn.
- **Weapons** produce immediate effects.
- **Oaths** reward a condition such as refusing to attack or stopping after the Oath.
- **Curses** damage, weaken, discard, or create debt.
- **Realms** provide a persistent board condition.
- At 0 Dharma, a player is **Unbalanced** and takes one additional damage from warrior attacks.
- Karma Debt counts down over two end phases, then deals damage equal to the outstanding debt.
- Health at 0 or lower ends the match.

## Online Room Flow

1. Start both servers.
2. Select **Create Room**, enter a display name, and create the room.
3. Copy the invite URL.
4. Open it in a second tab, browser profile, or another device that can reach the backend.
5. Each client sees only its own hand. The server validates turns and broadcasts every accepted action.

## Tests

```bash
cd astra-card-prototype/backend
pytest

cd ../frontend
npm run build
```

## Current Limitations

- Active rooms disappear when the backend restarts.
- There are no accounts, custom decks, matchmaking, spectators, or reconnect grace periods.
- Combat targets the rival leader in the current UI; the engine also supports warrior-to-warrior targets.
- The local TypeScript engine mirrors the Python rules but is separate code. A future production client should use the server for every mode.
- Balance, card copy limits, accessibility review, audio, and final artwork require further playtesting.

## Suggested Next Steps

Add deck construction and persistence, make the local demo server-authoritative, expose warrior targeting in the UI, add account-backed match history, and run structured balance telemetry before expanding beyond the two starter factions.
