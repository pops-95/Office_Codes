import React, { useEffect, useMemo, useRef, useState } from "react";
import { Bell, BellRing, Copy, Crown, Dice5, LogIn, MessageCircle, Pencil, Send, Users } from "lucide-react";
import { io } from "socket.io-client";
import Board from "./Board";

const API_URL = import.meta.env.VITE_API_URL || `${location.protocol}//${location.hostname}:5000`;
const socket = io(API_URL, { autoConnect: false });

function getPlayerId() {
  let id = localStorage.getItem("cdca-player-id");
  if (!id) {
    const browserCrypto = window.crypto;
    if (typeof browserCrypto?.randomUUID === "function") {
      id = browserCrypto.randomUUID();
    } else if (typeof browserCrypto?.getRandomValues === "function") {
      const bytes = browserCrypto.getRandomValues(new Uint8Array(16));
      id = Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join("");
    } else {
      id = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    }
    localStorage.setItem("cdca-player-id", id);
  }
  return id;
}

function playPing() {
  const AudioContext = window.AudioContext || window.webkitAudioContext;
  if (!AudioContext) return;
  const context = new AudioContext();
  const oscillator = context.createOscillator();
  const gain = context.createGain();
  oscillator.frequency.value = 720;
  gain.gain.setValueAtTime(0.08, context.currentTime);
  gain.gain.exponentialRampToValueAtTime(0.001, context.currentTime + 0.25);
  oscillator.connect(gain).connect(context.destination);
  oscillator.start();
  oscillator.stop(context.currentTime + 0.25);
}

export default function App() {
  const [name, setName] = useState(localStorage.getItem("cdca-name") || "");
  const [joinCode, setJoinCode] = useState("");
  const [homeTab, setHomeTab] = useState("create");
  const [maxPlayers, setMaxPlayers] = useState(4);
  const [room, setRoom] = useState(null);
  const [playerId, setPlayerId] = useState(getPlayerId);
  const [error, setError] = useState("");
  const [connected, setConnected] = useState(false);
  const [notifications, setNotifications] = useState(true);
  const [unread, setUnread] = useState(0);
  const [chatOpen, setChatOpen] = useState(true);
  const [now, setNow] = useState(Date.now());
  const roomRef = useRef(null);
  const playerRef = useRef(playerId);
  const notificationsRef = useRef(notifications);
  const chatOpenRef = useRef(chatOpen);

  useEffect(() => {
    roomRef.current = room;
    playerRef.current = playerId;
    notificationsRef.current = notifications;
    chatOpenRef.current = chatOpen;
  }, [room, playerId, notifications, chatOpen]);

  useEffect(() => {
    socket.connect();
    socket.on("connect", () => setConnected(true));
    socket.on("disconnect", () => setConnected(false));
    socket.on("room_joined", ({ playerId: joinedId, room: nextRoom }) => {
      setPlayerId(joinedId);
      localStorage.setItem("cdca-player-id", joinedId);
      setRoom(nextRoom);
      setError("");
    });
    socket.on("room_state", setRoom);
    socket.on("game_error", ({ message }) => setError(message));
    socket.on("chat_message", (message) => {
      setRoom((current) => current ? { ...current, messages: [...current.messages, message].slice(-100) } : current);
      if (message.senderId !== playerRef.current && notificationsRef.current) {
        playPing();
        if (!chatOpenRef.current) setUnread((value) => value + 1);
        if (document.hidden && "Notification" in window && Notification.permission === "granted") {
          new Notification(`${message.senderName} in CDCA Ludo`, { body: message.text });
        }
      }
    });
    return () => {
      socket.off();
      socket.disconnect();
    };
  }, []);

  useEffect(() => {
    const ticker = setInterval(() => setNow(Date.now()), 250);
    return () => clearInterval(ticker);
  }, []);

  const submitName = () => {
    const nextName = name.trim() || "Player";
    setName(nextName);
    localStorage.setItem("cdca-name", nextName);
    return nextName;
  };

  const createRoom = () => socket.emit("create_room", { name: submitName(), playerId, maxPlayers });
  const joinRoom = () => socket.emit("join_room", { code: joinCode, name: submitName(), playerId });

  const toggleNotifications = async () => {
    const next = !notifications;
    setNotifications(next);
    if (next && "Notification" in window && Notification.permission === "default") {
      await Notification.requestPermission();
    }
  };

  const toggleChat = () => {
    setChatOpen((value) => !value);
    setUnread(0);
  };

  if (!room) {
    return (
      <main className="landing">
        <div className="ambient ambient-one" />
        <div className="ambient ambient-two" />
        <section className="hero">
          <div className="mini-board" aria-hidden="true">
            <span className="mini red" /><span className="mini green" />
            <span className="mini blue" /><span className="mini yellow" />
            <div className="mini-center">★</div>
          </div>
          <p className="eyebrow">ROLL • RACE • RULE THE BOARD</p>
          <h1>CDCA <span>LUDO</span> TEAM</h1>
          <p className="hero-copy">Bring your crew together on the same Wi-Fi and turn every roll into a story.</p>
        </section>

        <section className="join-card">
          <div className="status-line">
            <span className={`status-dot ${connected ? "online" : ""}`} />
            {connected ? "Game server ready" : "Connecting to game server..."}
          </div>
          <label className="name-field">
            <span className="field-title"><Pencil size={15} /> Change your player name</span>
            <div className="input-wrap"><Users size={19} /><input value={name} onChange={(event) => setName(event.target.value)} maxLength={24} placeholder="Enter your name" /></div>
          </label>
          <div className="home-tabs" role="tablist">
            <button className={homeTab === "create" ? "active" : ""} onClick={() => { setHomeTab("create"); setError(""); }}><Dice5 size={18} /> Create Room</button>
            <button className={homeTab === "join" ? "active" : ""} onClick={() => { setHomeTab("join"); setError(""); }}><LogIn size={18} /> Join Room</button>
          </div>
          {homeTab === "create" ? (
            <div className="tab-content">
              <label className="invite-label">How many players?</label>
              <div className="player-count">
                {[2, 3, 4].map((count) => <button key={count} className={maxPlayers === count ? "active" : ""} onClick={() => setMaxPlayers(count)}>{count} players</button>)}
              </div>
              <p className="tab-help">You will receive a 4-digit invite code after creating the room.</p>
              <button className="primary create" onClick={createRoom} disabled={!connected}>
                <Dice5 size={22} /> Create room
              </button>
            </div>
          ) : (
            <div className="tab-content">
              <label className="invite-label" htmlFor="invite-code">Enter 4-digit invite code</label>
              <div className="join-row">
                <input
                  id="invite-code"
                  className="code-input"
                  value={joinCode}
                  onChange={(event) => setJoinCode(event.target.value.replace(/\D/g, "").slice(0, 4))}
                  onKeyDown={(event) => event.key === "Enter" && joinCode.length === 4 && joinRoom()}
                  maxLength={4}
                  inputMode="numeric"
                  pattern="[0-9]{4}"
                  autoComplete="one-time-code"
                  placeholder="0000"
                  aria-label="Four digit invite code"
                />
                <button className="primary join" onClick={joinRoom} disabled={!connected || joinCode.length !== 4}><LogIn size={20} /> Join</button>
              </div>
              <p className="tab-help">Ask the room creator for the code. You must be on the same network.</p>
            </div>
          )}
          {error && <p className="error">{error}</p>}
        </section>
      </main>
    );
  }

  const me = room.players.find((player) => player.id === playerId);
  const currentPlayer = room.players.find((player) => player.id === room.currentPlayerId);
  const seconds = room.turnDeadline ? Math.max(0, Math.ceil((room.turnDeadline * 1000 - now) / 1000)) : 15;
  const timerProgress = room.turnDeadline ? Math.max(0, Math.min(100, ((room.turnDeadline * 1000 - now) / (room.turnSeconds * 1000)) * 100)) : 100;
  const myTurn = room.currentPlayerId === playerId;
  const winner = room.players.find((player) => player.id === room.winnerId);
  const diceRolling = room.dice !== null && now < ((room.diceRolledAt || 0) * 1000 + 700);
  const diceRevealing = room.dice !== null && now < (room.diceAvailableAt || 0) * 1000;

  return (
    <main className="game-page">
      <header className="game-header">
        <div className="brand"><span className="brand-mark">★</span><div><small>CDCA</small><strong>LUDO TEAM</strong></div></div>
        <div className="room-code">ROOM <strong>{room.code}</strong><button onClick={() => navigator.clipboard.writeText(room.code)} title="Copy invite code"><Copy size={17} /></button></div>
        <div className="header-actions">
          <span className={`connection ${connected ? "online" : ""}`}>{connected ? "Online" : "Reconnecting"}</span>
          <button className="icon-button" onClick={toggleNotifications}>{notifications ? <BellRing size={20} /> : <Bell size={20} />}</button>
          <button className="icon-button chat-toggle" onClick={toggleChat}><MessageCircle size={20} />{unread > 0 && <b>{unread}</b>}</button>
        </div>
      </header>

      <section className={`game-layout ${chatOpen ? "" : "chat-hidden"}`}>
        <aside className="players-panel">
          <h2><Users size={19} /> Players</h2>
          {!room.started && <div className="lobby-count">{room.players.length} / {room.maxPlayers} positions filled</div>}
          <div className="player-list">
            {room.players.map((player) => (
              <PlayerCard key={player.id} player={player} isMe={player.id === playerId} isHost={player.id === room.hostId} isTurn={player.id === room.currentPlayerId} room={room} />
            ))}
            {!room.started && Array.from({ length: room.maxPlayers - room.players.length }, (_, index) => (
              <EmptyPlayerSlot key={`empty-${index}`} position={room.players.length + index + 1} />
            ))}
          </div>
          {!room.started && room.hostId === playerId && (
            <button className="primary start-button" disabled={room.players.length !== room.maxPlayers} onClick={() => socket.emit("start_game", { code: room.code, playerId })}>Start game</button>
          )}
          {!room.started && <p className="waiting">{room.players.length < room.maxPlayers ? `Waiting for ${room.maxPlayers - room.players.length} more player(s)...` : room.hostId === playerId ? "All positions filled. Start the game!" : "Waiting for the creator to start."}</p>}
          <RenameForm name={me?.name || name} onRename={(newName) => { setName(newName); localStorage.setItem("cdca-name", newName); socket.emit("rename", { code: room.code, playerId, name: newName }); }} />
        </aside>

        <section className="board-zone">
          {room.started && !winner && (
            <div className={`turn-banner ${myTurn ? "mine" : ""}`}>
              <div><span className={`color-dot ${currentPlayer?.color}`} />{myTurn ? "Your turn" : `${currentPlayer?.name}'s turn`}</div>
              <div className="turn-status">{diceRevealing ? "Dice rolling..." : `${seconds} seconds left`}</div>
            </div>
          )}
          {!room.started && <div className="turn-banner lobby-banner">Invite code <strong>{room.code}</strong> • {room.players.length}/{room.maxPlayers} joined</div>}
          {winner && <div className="winner-banner"><Crown size={25} /> {winner.name} wins!</div>}
          <Board room={room} playerId={playerId} now={now} onMove={(tokenIndex) => socket.emit("move_token", { code: room.code, playerId, tokenIndex })} />
          <div className="dice-console">
            <div className="dice-action">
              <button className={`dice ${diceRolling ? "rolling" : ""} ${currentPlayer?.color || ""}`} disabled={!room.started || !myTurn || room.dice !== null || !!winner} onClick={() => socket.emit("roll_dice", { code: room.code, playerId })}>
                {room.dice ? <DiceFace value={room.dice} /> : <DiceFace value={5} muted />}
              </button>
              {room.started && <div className="timer-progress" title={`${seconds} seconds remaining`}><span style={{ width: `${timerProgress}%` }} /></div>}
              {room.started && <small>{seconds}s</small>}
            </div>
            <div className="dice-copy"><strong>{!room.started ? "Game lobby" : myTurn ? room.dice ? diceRevealing ? "Watch the dice result" : "Choose a highlighted token" : "Roll the dice" : `Waiting for ${currentPlayer?.name}`}</strong><span>{room.started ? room.consecutiveSixes === 2 ? "Two sixes rolled; the next roll will be below six" : "A six or capture gives another turn" : `${room.maxPlayers} player room`}</span></div>
          </div>
        </section>

        {chatOpen && <Chat room={room} playerId={playerId} onSend={(text) => socket.emit("chat_message", { code: room.code, playerId, text })} />}
      </section>
      {error && <button className="toast" onClick={() => setError("")}>{error}</button>}
    </main>
  );
}

const DICE_PIPS = {
  1: [5],
  2: [1, 9],
  3: [1, 5, 9],
  4: [1, 3, 7, 9],
  5: [1, 3, 5, 7, 9],
  6: [1, 3, 4, 6, 7, 9],
};

function DiceFace({ value, muted = false }) {
  return (
    <span className={`dice-face ${muted ? "muted" : ""}`} aria-label={`Dice showing ${value}`}>
      {DICE_PIPS[value].map((position) => <i key={position} style={{ gridArea: `${Math.ceil(position / 3)} / ${((position - 1) % 3) + 1}` }} />)}
    </span>
  );
}

function PlayerCard({ player, isMe, isHost, isTurn, room }) {
  const finished = player.tokens.filter((token) => token === 57).length;
  return (
    <div className={`player-card ${isTurn ? "active" : ""}`}>
      <div className={`avatar ${player.color}`}>{player.name.charAt(0).toUpperCase()}</div>
      <div className="player-info"><strong>{player.name} {isMe && <em>You</em>}</strong><span>{finished}/4 home {!player.connected && "• offline"}</span></div>
      {isHost && <Crown size={17} className="crown" />}
      {isTurn && room.started && <span className="turn-pulse" />}
    </div>
  );
}

function EmptyPlayerSlot({ position }) {
  return (
    <div className="player-card empty-slot">
      <div className="avatar empty-avatar">{position}</div>
      <div className="player-info"><strong>Open position</strong><span>Waiting to join...</span></div>
    </div>
  );
}

function RenameForm({ name, onRename }) {
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState(name);
  useEffect(() => setValue(name), [name]);
  const save = () => {
    const clean = value.trim();
    if (clean) onRename(clean);
    setEditing(false);
  };
  return editing ? (
    <div className="rename-form"><input value={value} maxLength={24} onChange={(e) => setValue(e.target.value)} onKeyDown={(e) => e.key === "Enter" && save()} autoFocus /><button onClick={save}>Save</button></div>
  ) : <button className="rename-button" onClick={() => setEditing(true)}><Pencil size={15} /> Change my name</button>;
}

function Chat({ room, playerId, onSend }) {
  const [text, setText] = useState("");
  const listRef = useRef(null);
  const messages = useMemo(() => room.messages || [], [room.messages]);
  useEffect(() => listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" }), [messages]);
  const send = () => {
    if (!text.trim()) return;
    onSend(text);
    setText("");
  };
  const tag = (name) => setText((current) => `${current}${current && !current.endsWith(" ") ? " " : ""}@${name} `);
  return (
    <aside className="chat-panel">
      <div className="chat-head"><div><MessageCircle size={20} /><strong>Game chat</strong></div><span>{room.players.filter((p) => p.connected).length} online</span></div>
      <div className="tag-row">{room.players.filter((p) => p.id !== playerId).map((player) => <button key={player.id} onClick={() => tag(player.name)}>@{player.name}</button>)}</div>
      <div className="messages" ref={listRef}>
        {messages.length === 0 && <p className="empty-chat">No messages yet. Say hello!</p>}
        {messages.map((message) => message.system ? <div className="system-message" key={message.id}>{message.text}</div> : (
          <div className={`message ${message.senderId === playerId ? "mine" : ""} ${message.mentions?.includes(playerId) ? "mentioned" : ""}`} key={message.id}>
            <strong>{message.senderName}</strong><p>{message.text}</p><time>{new Date(message.timestamp * 1000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</time>
          </div>
        ))}
      </div>
      <div className="chat-input"><input value={text} onChange={(e) => setText(e.target.value)} onKeyDown={(e) => e.key === "Enter" && send()} placeholder="Write a message or tag @player..." /><button onClick={send}><Send size={19} /></button></div>
    </aside>
  );
}
