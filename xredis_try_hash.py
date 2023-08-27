import redis

if '__main__' == __name__:

    rdb = redis.Redis('127.0.0.1', 6379, 0)

    r = rdb.hset('map009', 'first_key', 'first_value_xxxx')  # hset = hash set
    print('r:', r)

    res = rdb.hget('map009', 'first_key').decode('utf8')  # hget = hash get
    print('first_key value:', res)
