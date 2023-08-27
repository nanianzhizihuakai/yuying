import datetime

from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks
import time
import redis
# import app.FIFO as FIFO  # TO-DO

BATCH_SIZE = 2

text_generation_zh_dict = pipeline(Tasks.text_generation, model='damo/nlp_gpt3_text-generation_chinese-base')
print('--------------------热身运动---------------------------------------')
text_generation_zh_dict('热身运动')
print('--------------------ALL IS READY---------------------------------------')

rdb = redis.Redis('127.0.0.1', 6379, 0)

# def text_generation_zh(xinput):
#     time.sleep(0.5)
#     return 'hello ' + xinput


def text_generation_zh(xinput):
    """
    推理函数
    :param xinput: list或str
    :return: list或str
    """
    # time.sleep(0.5)  # 我的失误，从假函数过渡过来，应该把这个去掉
    xresult = text_generation_zh_dict(xinput)
    xoutput_list = []
    if isinstance(xresult, list):
        for xel in xresult:
            xoutput_list.append(xel['text'])
        return xoutput_list
    else:
        xoutput = xresult['text']
        # print('MODEL SCOPE:', xoutput)
        return xoutput


while True:
    # 从redis 拿数据
    xuuid_list = []
    for i in range(BATCH_SIZE):
        xuuid = rdb.rpop('fifo')
        if xuuid is None:
            continue
        xuuid_list.append(xuuid)
    if not xuuid_list:
        time.sleep(0.001)  # 重要
        continue
    print(f'----- input: x{len(xuuid_list)} -------' + str(datetime.datetime.now()))
    xinput_list = []
    for xuuid in xuuid_list:
        xinput = rdb.hget('uuid2input', xuuid)
        if xinput is None:
            time.sleep(0.001)  # 重要
            continue
        xinput = xinput.decode('utf8')
        print(xinput)
        xinput_list.append(xinput)

    # 推理
    xoutput_list = text_generation_zh(xinput_list)
    print(f'----- output: x{len(xoutput_list)} -------' + str(datetime.datetime.now()))

    # 把数据放回
    for i, xuuid in enumerate(xuuid_list):
        xoutput = xoutput_list[i]
        rdb.hset('uuid2output', xuuid, xoutput.encode('utf8'))

    time.sleep(0.001)  # 重要
