import asyncio
import json
import os
from datetime import datetime

import websockets


PICARTO_TOKEN = os.getenv("PICARTO_TOKEN", "")
DATA_DIR = os.getenv("DATA_DIR", "/data")

if not PICARTO_TOKEN:
    raise RuntimeError("Please set PICARTO_TOKEN environment variable.")

uri = f"wss://chat.picarto.tv/chat/token={PICARTO_TOKEN}"


async def connect_and_communicate():
    os.makedirs(DATA_DIR, exist_ok=True)

    while True:
        current_date = datetime.now().strftime("%Y-%m-%d")
        file_name = os.path.join(DATA_DIR, f"{current_date}.txt")

        try:
            async with websockets.connect(uri) as websocket:
                await websocket.send(json.dumps({"type": "welcomeMessage"}))
                await websocket.send(json.dumps({"type": "accessLevelMessage"}))
                await websocket.send(json.dumps({"type": "multistreamMessage"}))
                await websocket.send(json.dumps({"type": "chatNext", "page": 1, "paginated": False}))
                await websocket.send(json.dumps({"type": "settings"}))
                await websocket.send(json.dumps({"type": "topChips"}))

                while True:
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=50)
                        response_json = json.loads(response)

                        if response_json.get("t") == "c":
                            with open(file_name, "a", encoding="utf-8") as file:
                                file.write(json.dumps(response_json, ensure_ascii=False) + "\n")

                            print(response_json, flush=True)

                    except asyncio.TimeoutError:
                        await websocket.send(json.dumps({"type": "ping", "message": "__ping__"}))

        except websockets.exceptions.ConnectionClosedError:
            print("Connection closed unexpectedly. Reconnecting in 10 seconds...", flush=True)
            await asyncio.sleep(10)

        except Exception as e:
            print(f"An error occurred: {e}. Retrying in 10 seconds...", flush=True)
            await asyncio.sleep(10)


asyncio.run(connect_and_communicate())
