#from fastapi import FastAPI
#import redis

#app = FastAPI()
#r = redis.Redis(host='localhost', port=7777)
#stream_name = "garrett"

#@app.get("/post/{message}")
#async def post(message : str):
#    r.xadd(stream_name, {'message': message})
#    return {"message": message}

#@app.get("/read/{last}")
#async def read(last: int):
#    return r.xread({'garrett': last})

from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

import aioredis
import redis
import uvicorn
import asyncio
import logging
import json

print("initializing")

REDIS_HOST = 'localhost'
REDIS_PORT = 7777
XREAD_TIMEOUT = 0
XREAD_COUNT = 100
NUM_PREVIOUS = 30
STREAM_MAX_LEN = 1000

app = FastAPI()
stream_name = "garrett"
r = redis.Redis(host='localhost', port=7777)
red = aioredis.from_url("redis://localhost:7777")

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://localhost:8000/ws");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""


async def get_new_messages(websocket):
    """
    wait for new items on chat stream and
    """
    last_id = 0
    while True:
        data = await red.xread(streams={stream_name: last_id})
        if data:
            messages = data[0][1:][0]
            for _id, message in messages:
                await websocket.send_text(str(message))
                last_id = _id
                print(last_id)


async def post_new_messages(websocket):
    while True:
        message = await websocket.receive_text()
        await red.xadd(stream_name, {'message': message})


@app.get("/")
async def get():
    return HTMLResponse(html)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    task1 = asyncio.create_task(get_new_messages(websocket))
    task2 = asyncio.create_task(post_new_messages(websocket))
    await task1
    await task2
