import { ArrowRight, Copy, RadioTower } from "lucide-react";
import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

export function CreateRoomPage() {
  const [name, setName] = useState("Oathkeeper");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  async function createRoom(event: FormEvent) {
    event.preventDefault();
    setLoading(true); setError("");
    try {
      const response = await fetch(`${API}/rooms`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ player_name: name }),
      });
      if (!response.ok) throw new Error("The backend did not create a room.");
      const result = await response.json();
      sessionStorage.setItem(`astra-room-${result.room_id}`, result.player_id);
      localStorage.setItem("astra-player-name", name);
      navigate(`/room/${result.room_id}`);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not reach the astral link.");
    } finally { setLoading(false); }
  }
  return (
    <div className="page room-create">
      <div className="room-panel">
        <span className="room-icon"><RadioTower /></span>
        <span className="eyebrow">ONLINE ROOM PROTOTYPE</span>
        <h1>Open an astral link</h1>
        <p>Create a six-character room code. Share the resulting URL with a second browser tab or another player.</p>
        <form onSubmit={createRoom}>
          <label>Display name<input required maxLength={30} value={name} onChange={(event) => setName(event.target.value)} /></label>
          <button className="primary-button" disabled={loading}>{loading ? "Opening link..." : "Create room"} <ArrowRight /></button>
        </form>
        {error && <div className="form-error">{error} Start FastAPI on port 8000 and try again.</div>}
        <div className="room-steps"><span><b>1</b> Create</span><span><Copy /><b>2</b> Share</span><span><b>3</b> Duel</span></div>
      </div>
    </div>
  );
}
