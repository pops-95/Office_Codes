import { Check, Copy, RadioTower } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { GameBoard } from "../components/GameBoard";
import type { GameState } from "../game/types";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";
const WS = API.replace(/^http/, "ws");

export function RoomPage() {
  const { roomId = "" } = useParams();
  const [game, setGame] = useState<GameState | null>(null);
  const [playerIndex, setPlayerIndex] = useState(0);
  const [notice, setNotice] = useState("Connecting to the room...");
  const [connected, setConnected] = useState(false);
  const [copied, setCopied] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);
  const tokenRef = useRef(sessionStorage.getItem(`astra-room-${roomId}`) || "");

  useEffect(() => {
    const socket = new WebSocket(`${WS}/ws/rooms/${roomId}`);
    socketRef.current = socket;
    socket.onopen = () => socket.send(JSON.stringify({
      type: "join", player_id: tokenRef.current || null,
      player_name: localStorage.getItem("astra-player-name") || "Challenger",
    }));
    socket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type === "joined") {
        tokenRef.current = message.player_id;
        setPlayerIndex(message.player_index);
        sessionStorage.setItem(`astra-room-${roomId}`, message.player_id);
        setConnected(true); setNotice("Astral link established.");
      } else if (message.type === "state") {
        setGame(message.state);
        setPlayerIndex(message.player_index);
        const count = message.state.players.filter((player: { name: string }) => player.name !== "Awaiting challenger").length;
        setNotice(count < 2 ? "Room open. Share the URL with your challenger." : message.state.log.at(-1));
      } else if (message.type === "error") setNotice(message.message);
    };
    socket.onerror = () => setNotice("Could not connect. Is FastAPI running on port 8000?");
    socket.onclose = () => setConnected(false);
    return () => socket.close();
  }, [roomId]);

  const send = useCallback((action: object) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ ...action, player_id: tokenRef.current }));
    }
  }, []);
  async function copyInvite() {
    await navigator.clipboard.writeText(window.location.href);
    setCopied(true); setTimeout(() => setCopied(false), 1500);
  }
  if (!game) return <div className="loading-page"><RadioTower /><h1>Seeking room {roomId}</h1><p>{notice}</p></div>;
  const challengerReady = game.players[1].name !== "Awaiting challenger";
  return (
    <div className="game-page">
      <div className="room-header">
        <div><span>ROOM CODE</span><strong>{roomId.toUpperCase()}</strong></div>
        <button onClick={copyInvite}>{copied ? <Check /> : <Copy />}{copied ? "Copied" : "Copy invite URL"}</button>
      </div>
      <GameBoard
        game={game} playerIndex={playerIndex} notice={notice} connected={connected && challengerReady}
        onPlay={(card_index) => send({ type: "play_card", card_index })}
        onAttack={(attacker_index) => send({ type: "attack", attacker_index })}
        onEnd={() => send({ type: "end_turn" })}
      />
    </div>
  );
}
