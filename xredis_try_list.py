import redis

if '__main__' == __name__:

    rdb = redis.Redis('127.0.0.1', 6379, 0)
    # rdb.lpush('list003', '我是第1个'.encode('utf8'))
    # rdb.lpush('list003', '我是第2个'.encode('utf8'))
    # rdb.lpush('list003', '我是第3个'.encode('utf8'))
    # rdb.lpush('list003', '我是第4个'.encode('utf8'))
    # rdb.lpush('list003', '我是第5个'.encode('utf8'))

    xlist = rdb.lrange('list003', 0, -1)
    # print(xlist)
    xlist = [el.decode('utf8') for el in xlist]
    print(xlist)

    r = rdb.rpop('list003')
    print('result:', r)

    xlist = rdb.lrange('list003', 0, -1)
    # print(xlist)
    xlist = [el.decode('utf8') for el in xlist]
    print(xlist)
