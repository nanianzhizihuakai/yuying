import pymongo as pm
from common import USER, KEY, VALUE

INDEXES = {
    "user_key": {
        "cols": [
            (USER, pm.ASCENDING),
            (KEY, pm.ASCENDING),
        ],
        "uniq": True
    },
    "user_key_desc": {
        "cols": [
            (USER, pm.DESCENDING),
            (KEY, pm.DESCENDING),
        ],
        "uniq": True
    },
    "gkey": {
        "cols": [
            ('gkey', pm.ASCENDING),
        ],
        "uniq": True
    }
}


def setup_indexes(db, tbl_name, index_names):
    """
    建立索引，如果已经有了，则跳过。
    :param db: mongodb实例
    :param tbl_name: 表名
    :param index_names: 索引名字（必须是INDEXES里面指定的索引名。）
    :return: None
    """
    tbl = db[tbl_name]
    indexes = set(tbl.index_information().keys())
    for index_name in index_names:
        index_spec = INDEXES[index_name]
        if not index_name in indexes:
            tbl.create_index(
                index_spec["cols"],
                unique=index_spec["uniq"],
                name=index_name,
            )
            print(f'mongodb: Created index {index_name} in table {tbl_name}')


def mongo_upsert(db, tbl_name, user, key, value, index_names=('user_key', 'user_key_desc', 'gkey', )):
    """
    upsert = update or insert
    有数据则更新，无则插入。
    :param db: mongodb实例
    :param tbl_name: 表名
    :param user: 用户名
    :param key: 键（一般都是纳秒时间戳）
    :param value: 值 （如果是dict则按key-value插入值，如果不是dict则用键名'value'插入。）
    :param index_names: 要建立的索引名字（必须是INDEXES里面指定的索引名。）（如果已经存在则跳过。）
    :return: None
    """
    tbl = db[tbl_name]
    query = {
        USER: user,
        KEY: key,
    }
    data = query.copy()
    data['gkey'] = f'{key},{user}'
    if isinstance(value, dict):
        for k in value.keys():
            data[k] = value[k]
    else:
        data[VALUE] = value

    # upsert
    tbl.find_one_and_update(  # find_one_and_update = find_one + update
        query,
        {
            '$set': data,
        },
        upsert=True
    )

    # handle the indexes
    setup_indexes(db, tbl_name, index_names)


def enqueue(db, tbl_name, user, key, value, index_names=('user_key', 'user_key_desc', 'gkey', )):
    """
    入队
    :param db: mongodb实例
    :param tbl_name: 表名
    :param user: 用户名
    :param key: 键（除了配置表conf，一般都是纳秒时间戳）
    :param value: 值 （如果是dict则按key-value插入值，如果不是dict则用键名'value'插入。）
    :param index_names: 要建立的索引名字（必须是global_conf["indexes"]里面指定的索引名。）（如果已经存在则跳过。）
    :return: None
    """
    mongo_upsert(db, tbl_name, user, key, value, index_names)

    # handle the indexes
    setup_indexes(db, tbl_name, index_names)


def dequeue(db, tbl_name, user=None, is_just_peek=True, order=pm.ASCENDING):
    """
    出队
    :param db: mongodb实例
    :param tbl_name: 表名
    :param user: 用户名
    :param is_just_peek: 是否获取后仍保留在队列里。
    :param order: 获取最早还是最晚
    :return: dict
    """
    tbl = db[tbl_name]

    if user is not None:
        query = {
            USER: user
        }
        sort = [
            (USER, order),
            (KEY, order),
        ]
    else:
        query = {}
        sort = [
            ('gkey', order)
        ]

    if is_just_peek:
        row = tbl.find_one(query, sort=sort)
    else:
        row = tbl.find_one_and_delete(query, sort=sort)
    return row


def get_sorted_by_key(db, tbl_name, user, limit=None, is_keep_others=True, return_cursor=False):
    """
    按倒序获取一定量的数据
    主要使用场景：获取最近的一些聊天记录。
    :param db: mongodb实例
    :param tbl_name: 表名
    :param user: 用户名
    :param limit: 指定出队几条，为None时不做限制。
    :param is_keep_others: 其他数据是否保留
    :param return_cursor: 是否返回cursor
    :return: cursor or list of dict
    """
    tbl = db[tbl_name]
    query = {
        USER: user,
    }
    cursor = tbl.find(query).sort([
        (USER, pm.DESCENDING),
        (KEY, pm.DESCENDING),
    ])
    if limit is not None:
        cursor.max_scan(limit + 1)
    if return_cursor:
        return cursor
    results = []
    border_ts = None
    for row in cursor:
        border_ts = row[KEY]
        results.append(row)

    if len(results) and not is_keep_others and limit is not None and border_ts is not None:
        tbl.delete_many({
            USER: user,
            KEY: {
                '$lt': border_ts
            }
        })

    return results


def delete_many_by_user(db, tbl_name, user, criteria={}):
    """
    按用户，按条件批量删除。
    :param db: mongodb实例
    :param tbl_name: 表名
    :param user: 用户名
    :param criteria: 条件
    :return: None
    """
    tbl = db[tbl_name]
    criteria[USER] = user
    tbl.delete_many(criteria)

    