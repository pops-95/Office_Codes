from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_and_cards_endpoints():
    assert client.get("/health").status_code == 200
    cards = client.get("/cards").json()
    assert len(cards) == 40
    assert {card["faction"] for card in cards} == {"Oathbound", "Night Court"}


def test_room_creation_and_public_state_hides_hands():
    created = client.post("/rooms", json={"player_name": "Test Keeper"})
    assert created.status_code == 200
    payload = created.json()
    assert len(payload["state"]["players"][0]["hand"]) == 5

    public = client.get(f"/rooms/{payload['room_id']}")
    assert public.status_code == 200
    assert public.json()["state"]["players"][0]["hand"] == []


def test_two_players_join_room_and_receive_state():
    payload = client.post("/rooms", json={"player_name": "Keeper"}).json()
    room_id = payload["room_id"]
    with client.websocket_connect(f"/ws/rooms/{room_id}") as first:
        first.send_json({"type": "join", "player_id": payload["player_id"], "player_name": "Keeper"})
        assert first.receive_json()["type"] == "joined"
        first.receive_json()
        with client.websocket_connect(f"/ws/rooms/{room_id}") as second:
            second.send_json({"type": "join", "player_name": "Challenger"})
            joined = second.receive_json()
            assert joined["type"] == "joined"
            assert joined["player_index"] == 1
            first_state = first.receive_json()
            second_state = second.receive_json()
            assert first_state["state"]["players"][1]["name"] == "Challenger"
            assert second_state["state"]["players"][0]["hand"] == []
