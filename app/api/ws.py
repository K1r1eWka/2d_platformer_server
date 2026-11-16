import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.connection_manager import manager

router = APIRouter()


# Подключение игрока к комнате: регистрация, оповещение остальных и релей сообщений.
@router.websocket("/ws/{room_id}")
async def game_room(websocket: WebSocket, room_id: str, client_id: str | None = None):
    client_id = client_id or uuid.uuid4().hex

    await manager.connect(room_id, client_id, websocket)
    print(f"Client connected: {client_id} to room: {room_id}")

    # Клиент узнаёт свой id и кто уже в комнате.
    await manager.send_personal_message(
        {
            "type": "connected",
            "client_id": client_id,
            "room_id": room_id,
            "players": [cid for cid in manager.get_clients(room_id) if cid != client_id],
        },
        websocket
    )
    await manager.broadcast(
                            room_id, 
                            {"type": "player_joined", "client_id": client_id}, 
                            client_id
                            )

    try:
        while True:
            data = await websocket.receive_json()
            # Send the received message to all other players in the room but not to sender
            await manager.broadcast(room_id, {**data, "client_id": client_id}, client_id)
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(room_id, client_id)
        print(f"Client disconnected: {client_id} from room: {room_id}")
        await manager.broadcast(
            room_id, {"type": "player_left", "client_id": client_id}, client_id
        )
