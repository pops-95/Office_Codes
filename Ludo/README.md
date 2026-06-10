# CDCA LUDO TEAM

A real-time, invite-only Ludo game for 2–4 players on the same local network.

## Run locally

Open two terminals from this folder.

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173`. Other devices on the same Wi-Fi can use
`http://HOST_LAN_IP:5173`.

The frontend connects to port `5000` on the same host by default. Set
`VITE_API_URL` when the backend is hosted elsewhere.

## Features

- Four-digit invite rooms restricted to the host's `/24` IPv4 or `/64` IPv6 network
- Editable player names and reconnectable browser identity
- Real-time chat, player tags, sound alerts, and browser notifications
- Server-authoritative dice, movement, captures, safe spaces, and wins
- 15-second turn timer with automatic roll/move fallback
- Click-to-select legal tokens when more than one move is available
