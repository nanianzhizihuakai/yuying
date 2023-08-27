import datetime
from util_mongo import (
    mongo_upsert,
    enqueue,
    dequeue,
    get_sorted_by_key,
    delete_many_by_user,
)
import pymongo as pm
import time

# 连接Mongodb
mongo = pm.MongoClient('127.0.0.1', 27017, serverSelectionTimeoutMS=3000)
mdb = mongo['test_db001']

# ts = time.time_ns()
# enqueue(mdb, 'test001', 'user001', ts, 'test001 user001的数据9999')
#
# ts = time.time_ns()
# enqueue(mdb, 'test001', 'user001', ts, {
#     'value': 'test001 user001的数据9998',
#     'duration': 1.5,
#     'dt': datetime.datetime.now(),
# })

# xresult = dequeue(mdb, 'test001', 'user001')
# print(xresult)

xresult = get_sorted_by_key(mdb, 'test001', 'user001')
print(xresult)
