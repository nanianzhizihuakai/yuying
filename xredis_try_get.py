import redis

if '__main__' == __name__:

    rdb = redis.Redis('127.0.0.1', 6379, 0)
    value = rdb.get('key001')
    print(value)
    value = value.decode('utf-8')
    print(value)
