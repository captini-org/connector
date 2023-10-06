import asyncio
import websockets
import json
import asyncio
import websockets
import json
import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
WEB_SOCKET_HOST = os.environ['WEB_SOCKET_HOST']
WEB_SOCKET_PORT = os.environ['WEB_SOCKET_PORT']
# Maintain a list of connected clients
connected_clients = set()

async def server(websocket, path):
    try:
        # Add the client to the list of connected clients
        connected_clients.add(websocket)

        while True:
            body = await websocket.recv()
            message= json.loads(body)
            print(f"Received from client: {body}")


            # Send the response message to all connected clients
            for client in connected_clients:
                await client.send(json.dumps(message))
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        # Remove the client from the list when they disconnect
        connected_clients.remove(websocket)

# Your dynamic message here
dynamic_message = "Insaf"

def start_server():
    # Start the WebSocket server
    s_server = websockets.serve(server, WEB_SOCKET_HOST,WEB_SOCKET_PORT)
    print('connected')
    print(s_server)
    # Run the event loop
    asyncio.get_event_loop().run_until_complete(s_server)
    asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
    start_server()
