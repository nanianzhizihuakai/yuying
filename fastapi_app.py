from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn
import redis
import time
from util import md5, uuid
import asyncio

app = FastAPI()
rdb = redis.Redis('127.0.0.1', 6379, 0)
PWD = 'password001'

@app.post("/api", response_class=JSONResponse)
async def do_infer(request: Request):
    req_json = await request.json()  # 请求json
    xinput = req_json['input']

    # 鉴权
    xcheck = req_json['check']
    xmy_check = xinput + PWD
    xmy_check = md5(xmy_check)
    if xcheck != xmy_check:
        return None

    # uuid
    xuuid = uuid()

    # 放入队列
    rdb.lpush('fifo', xuuid)
    rdb.hset('uuid2input', xuuid, xinput.encode('utf8'))

    # 后台从队列拿数据，推理，结果放入hash

    # 从hash拿结果（轮询）
    while True:
        xoutput = rdb.hget('uuid2output', xuuid)
        if xoutput is None:
            await asyncio.sleep(0.001)  # 重要
            continue
        else:
            rdb.hdel('uuid2input', xuuid)
            rdb.hdel('uuid2output', xuuid)
            xoutput = xoutput.decode('utf8')
            break

    res_json = dict()
    res_json['input'] = xinput
    res_json['output'] = xoutput
    # https://stackoverflow.com/questions/71794990/fast-api-how-to-return-a-str-as-json
    return JSONResponse(content=res_json)


if '__main__' == __name__:

    # https://stackoverflow.com/questions/63177681/is-there-a-difference-between-running-fastapi-from-uvicorn-command-in-dockerfile
    uvicorn.run('fastapi_app:app', host='0.0.0.0', port=7777)
