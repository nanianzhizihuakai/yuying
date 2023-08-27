import redis

if '__main__' == __name__:

    rdb = redis.Redis('127.0.0.1', 6379, 0)
    r = rdb.set('key001', '文本001 text001'.encode('utf-8'))
    print('result:', r)
