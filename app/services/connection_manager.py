from fastapi import WebSocket, WebSocketDisconnect

# Errors that mean the connection is already dead, so the client can be dropped.
# Anything else (e.g. TypeError from a message that is not JSON serializable)
DEAD_CONNECTION_ERRORS = (WebSocketDisconnect, ConnectionError, RuntimeError)


class RoomConnectionManager:

    # {room_id: {client_id: websocket}}
    def __init__(self) -> None:
        self.rooms: dict[str, dict[str, WebSocket]] = {}


    # Accepts a websocket connection and adds the player to the room.
    async def connect(self, room_id: str, client_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.rooms.setdefault(room_id, {})[client_id] = websocket


    # Removes a player from the room. An empty room is deleted entirely
    def disconnect(self, room_id: str, client_id: str) -> None:
        room = self.rooms.get(room_id)
        if room is None:
            return

        # pop return None if the client was not in the room.
        room.pop(client_id, None)
        if not room:
            self.rooms.pop(room_id, None)


    # Broadcasts a message to everyone in the room except the sender. items() converts the dictionary to a list of key-value pairs like: [('alice', 'ws_A'), ('bob', 'ws_B')]
    async def broadcast(self, room_id: str, message: dict, sender_id: str | None = None) -> None:
        for client_id, websocket in list(self.rooms.get(room_id, {}).items()):
            if client_id == sender_id:
                continue
            try:
                await websocket.send_json(message)
            except DEAD_CONNECTION_ERRORS:
                self.disconnect(room_id, client_id)


    # Sends a message to a single player.
    async def send_personal_message(self, message: dict, websocket: WebSocket) -> None:
        await websocket.send_json(message)


    # Who is currently in the room.
    def get_clients(self, room_id: str) -> list[str]:
        return list(self.rooms.get(room_id, {}))


# Global object for all server connections
manager = RoomConnectionManager()
