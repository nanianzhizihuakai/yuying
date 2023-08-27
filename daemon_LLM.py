import datetime
from modelscope.utils.constant import Tasks
from modelscope import Model
from modelscope.pipelines import pipeline
import time
import redis
# import app.FIFO as FIFO  # TO-DO
import pymongo as pm
from common import MONGODB_NAME, VALUE, KEY, IO_PREFIX, RATE
from util import uuid, merge_dialog_in_and_out, translate_ns, compose_wav_header
from util_mongo import (
    enqueue,
    dequeue,
    get_sorted_by_key,
)

BATCH_SIZE = 2

# text_generation_zh_dict = pipeline(Tasks.text_generation, model='damo/nlp_gpt3_text-generation_chinese-base')
# print('--------------------热身运动---------------------------------------')
# text_generation_zh_dict('热身运动')

model = Model.from_pretrained('ZhipuAI/chatglm2-6b', device='cuda', revision='v1.0.7')
pipe = pipeline(task=Tasks.chat, model=model)


# def pipe(xinput_list):
#     xoutput = [{
#         'response': 'Fake output' + str(datetime.datetime.now()),
#         'history': []
#     }, {
#         'response': 'Fake 002' + str(datetime.datetime.now()),
#         'history': []
#     }]
#     return xoutput


# 连接Mongodb
mongo = pm.MongoClient('127.0.0.1', 27017, serverSelectionTimeoutMS=3000)
mdb = mongo[MONGODB_NAME]
# 连接redis
rdb = redis.Redis('127.0.0.1', 6379, 0)


# def text_generation_zh(xinput):
#     time.sleep(0.5)
#     return 'hello ' + xinput


def text_generation_zh(xinput_list, xhistory_list):
    """
    推理函数
    :param xinput: list 各个用户当前输入
    :return: list 各个用户聊天历史
    """
    # 构建传入参数
    xarg_list = []
    for i, xinput in enumerate(xinput_list):
        xdict = dict()
        xdict['text'] = xinput
        xdict['history'] = xhistory_list[i]
        xarg_list.append(xdict)

    # 推理
    xresult = pipe(xarg_list)

    # 拼装放回列表
    xoutput_list = []
    for xdict in xresult:
        xoutput_list.append(xdict['response'])
    return xoutput_list


def update_chat_history(username):
    """
    刷新聊天记录的handler

    :param username:
    :return: list of list
    """
    if username is None:
        return []

    rows_in = get_sorted_by_key(mdb, 'dialog_in', username)  # DESC
    rows_out = get_sorted_by_key(mdb, 'dialog_out', username)  # DESC
    rows = merge_dialog_in_and_out(rows_in, rows_out)  # DESC
    rows = rows[::-1]  # ASC

    if not len(rows):
        log = []
    else:
        log = []
        pair = [None, None]
        for row in rows:
            xstr = row[VALUE]
            # timestamp = row[KEY]
            # dt_str = translate_ns(timestamp)
            # xstr = IO_PREFIX.get(row["io"], '?') + ': '
            # xstr += f'[ {dt_str} ] '
            # xstr += text

            if 'i' == row['io']:
                if pair[0] is not None or pair[1] is not None:
                    log.append(pair)
                    pair = [xstr, None]
                    continue
                pair[0] = xstr
            elif 'o' == row['io']:
                if pair[1] is not None:
                    log.append(pair)
                    pair = [None, xstr]
                    continue
                pair[1] = xstr
        log.append(pair)

    logs = []
    for xel in log:
        logs.append(tuple(xel))

    return logs


print('--------------------ALL IS READY---------------------------------------')
while True:
    # 从redis 拿uuid
    xuuid_list = []
    for i in range(BATCH_SIZE):
        xuuid = rdb.rpop('fifo')
        if xuuid is None:
            continue
        xuuid_list.append(xuuid)
    if not xuuid_list:
        time.sleep(0.001)  # 重要
        continue

    # 从redis 拿input和username
    print(f'----- input: x{len(xuuid_list)} -------' + str(datetime.datetime.now()))
    xinput_list = []
    xusername_list = []
    xhistory_list = []
    for xuuid in xuuid_list:

        # 拿input
        xinput = rdb.hget('uuid2input', xuuid)
        if xinput is None:
            time.sleep(0.001)  # 重要
            continue
        xinput = xinput.decode('utf8')
        print('input:', xinput)
        xinput_list.append(xinput)

        # 拿username
        xusername = rdb.hget('uuid2username', xuuid)
        if xusername is None:
            time.sleep(0.001)  # 重要
            continue
        xusername = xusername.decode('utf8')
        print('username:', xusername)
        xusername_list.append(xusername)

        # 从Username找聊天历史
        xhistory = update_chat_history(xusername)
        print('history:', xhistory)
        xhistory_list.append(xhistory)

    # 推理
    xoutput_list = text_generation_zh(xinput_list, xhistory_list)
    print(f'----- output: x{len(xoutput_list)} -------' + str(datetime.datetime.now()))

    # 把数据放回
    for i, xuuid in enumerate(xuuid_list):
        xoutput = xoutput_list[i]
        rdb.hset('uuid2output', xuuid, xoutput.encode('utf8'))

    time.sleep(0.001)  # 重要
