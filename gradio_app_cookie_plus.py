"""
【注意】还在debug中！
"""
import time
import gradio as gr
from app_test import text_gen
from util import uuid
from http.cookies import SimpleCookie
from util_mongo import (
    mongo_upsert,
    enqueue,
    dequeue,
    get_sorted_by_key,
    delete_many_by_user,
)
import pymongo as pm
from common import MONGODB_NAME, VALUE, KEY, IO_PREFIX

# 连接Mongodb
mongo = pm.MongoClient('127.0.0.1', 27017, serverSelectionTimeoutMS=3000)
mdb = mongo['test_db001']

def embed_user_id_in_state_comp(request: gr.Request):
    """
    页面加载的事件handler

    从HTTP request中获取cookie来确定用户名，如果没有则生成一个
    :param request: HTTP request JSON
    :return: 将用户名发送给浏览器和存放用户名的组件
    """
    xuuid = uuid()

    #从cookie中获取username
    username = None
    try:
        cookie_str = request.headers.cookie
        print('cookie_str:', cookie_str)
        cookie = SimpleCookie()
        cookie.load(cookie_str)
        username = cookie.get('username', None)
        print('user:', username)
        username = username.value
    except Exception:
        try:
            username = request.cookies['username']
        except Exception:
            pass

    # 获取不到，新建一个username
    if username is None:
        print('new user!')
        username = f'u{xuuid}'

    # print username
    print('user:', username)

    # 获取历史
    xpair_list = show_chat_history(username)

    return username, username, username, xpair_list


def show_chat_history(username):
    """

    [
        [in, out],
        [in, out],
        [in, None],
    ]

    # 理想结果
    [
        [in, None],
        [in, None],
        [in, out],
    ]

    # 目前一期做法
    [
        [in, in]
        [in, out]
    ]

    # 算法
    [1, 2, 3, 4, 5]
    [
        [1, 2],
        [3, 4],
        [5, None],
    ]

    [in, out]
    =>
    [
        [out, in]
    ]

    :param username:
    :return:
    """
    if username is None:
        return []

    # 获取数据
    xhis = get_sorted_by_key(mdb, 'dialog', username)
    xhis = xhis[::-1]

    # 如果没有数据
    if not xhis:
        return []

    # 组织数据
    xpair_list = []
    xpair = []
    for xel in xhis:

        # 组织字符串 “输入：XXXXXX” 或 “输出: XXXXXXX”
        xsent = xel[VALUE]
        xio = xel['io']
        xio = IO_PREFIX[xio]
        xsent = xio + ': ' + xsent

        if len(xpair) >= 2:
            xpair_list.append(xpair)
            xpair = []
        else:
            xpair.append(xsent)
    if len(xpair) < 2:
        xpair.append(None)
    xpair_list.append(xpair)
    return xpair_list


def save_input(username, xinput):
    if username is None:
        return [], ''

    # 入库
    ts = time.time_ns()
    enqueue(mdb, 'dialog', username, ts, {
        VALUE: xinput,
        'io': 'i',
    })

    # 获取历史
    xpair_list = show_chat_history(username)
    return xpair_list, ''


def handle_click(username, xinput):
    if username is None:
        return [], ''

    # 推理
    xoutput = text_gen(xinput)

    # 入库
    ts = time.time_ns()
    enqueue(mdb, 'dialog', username, ts, {
        VALUE: xoutput,
        'io': 'o',
    })

    # 获取历史
    xpair_list = show_chat_history(username)
    return xpair_list, ''


# 用户名写入cookie的JS
js_username2cookie = """
    async () => {{
            setTimeout(() => {{
                var xnew = document.querySelector('#username.prose').innerHTML;
                //console.log('username', xnew)
                if ('' == xnew) {
                    return;
                }
                document.cookie = 'username=' + xnew + '; max-age=' + 3600*24*30*6;
            }}, 1);
        }}
"""

with gr.Blocks(analytics_enabled=False) as demo:
    # 用户名
    cmp_username_state = gr.State()
    cmp_username_html = gr.HTML(visible=False, elem_id='username')
    cmp_username_display = gr.Textbox(interactive=False, label='用户名')

    # 历史控件
    cmp_chat_history = gr.Chatbot().style(height=350)

    # 输入输出控件
    xinput = gr.Textbox(interactive=True, label='输入')
    xinput_button = gr.Button('发送')
    # xoutput = gr.Textbox(interactive=False, label='输出')

    # 按钮点击事件
    xinput_button.click(save_input, [cmp_username_state, xinput], [cmp_chat_history, xinput])
    xinput_button.click(handle_click, [cmp_username_state, xinput], [cmp_chat_history, xinput])

    # 加载时获取或设置cookie 加载聊天历史
    demo.load(embed_user_id_in_state_comp, None, [
        cmp_username_state,
        cmp_username_display,
        cmp_username_html,
        cmp_chat_history
    ])
    # cmp_username_html发生变化时，触发JS，把生成的username放入页面cookie
    cmp_username_html.change(None, None, None, _js=js_username2cookie, queue=False)  # hack



# 用gradio启动，但是这样queue就不正常，可能还是得用uvicorn启动
# demo.launch(server_name='0.0.0.0', server_port=7776, share=True, debug=True)
demo.launch(server_name='0.0.0.0', server_port=7776, debug=True)
