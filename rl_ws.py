import asyncio
import websockets
import json

class RLWebSocketClient:
    def __init__(self, url, event_queue):
        self.url = url
        self.websocket = None
        self.event_queue = event_queue
        self.loop = asyncio.get_event_loop()

    async def connect(self):
        self.websocket = await websockets.connect(self.url)
        print(f"Connected to {self.url}")
        await self.listen()

    async def listen(self):
        try:
            async for message in self.websocket:
                await self.on_message(message)
        except websockets.exceptions.ConnectionClosed as e:
            await self.on_close(e.code, e.reason)
        except Exception as e:
            await self.on_error(str(e))

    async def on_message(self, message):
        await self.event_queue.put(message)
        print(f"Received message: {message}")

    async def on_error(self, error):
        print(f"Error: {error}")

    async def on_close(self, close_status_code, close_msg):
        print(f"WebSocket connection closed: {close_status_code}, {close_msg}")

    async def process_command(self, command, data):
        if command == "replay:skip_back":
            await self.skip_back()
        elif command == "replay:focus_player":
            await self.focus_player(data["platform"], data["actor_id"])

    async def send_command(self, command):
        if self.websocket:
            await self.websocket.send(json.dumps(command))
            print(f"Sent command: {json.dumps(command)}")

    async def focus_player(self, platform, actor_id):
        command = {
            "event": "replay:focus_player",
            "data": {
                "platform": platform,
                "actor_id": actor_id
            }
        }
        await self.send_command(command)

    async def skip_back(self):
        command = {
            "event": "replay:skip_back",
            "data": "replay_skip_back"
        }
        await self.send_command(command)

    def run(self):
        self.loop.run_until_complete(self.connect())
        self.loop.run_forever()
