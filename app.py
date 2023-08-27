from flask import Flask, url_for, request
import redis
import time
from util import md5, uuid

app = Flask(__name__)
rdb = redis.Redis('127.0.0.1', 6379, 0)
PWD = 'password001'

@app.route("/api", methods=['POST'])
def do_infer():
    req_json = request.get_json(force=True)  # 请求json
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
            time.sleep(0.001)  # 重要
            continue
        else:
            rdb.hdel('uuid2input', xuuid)
            rdb.hdel('uuid2output', xuuid)
            xoutput = xoutput.decode('utf8')
            break

    res_json = dict()
    res_json['input'] = xinput
    res_json['output'] = xoutput
    return res_json


if '__main__' == __name__:
    # 启动方式1： 启动命令
    # flask run --host=0.0.0.0 --port=7777

    # 启动方式2： 在这里启动
    # https://www.cnblogs.com/chaojiyingxiong/p/14988069.html
    app.run('0.0.0.0', 7777)
