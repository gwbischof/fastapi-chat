from fastapi import FastAPI
import redis

app = FastAPI()
r = redis.Redis(host='localhost', port=7777)
stream_name = "garrett"

@app.get("/post/{message}")
async def post(message : str):
    r.xadd(stream_name, {'message': "hello"})
    return {"message": message}

@app.get("/read")
async def read():
    return r.xread({'garrett': 0})
