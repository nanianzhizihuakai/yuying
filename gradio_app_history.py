import time
import gradio as gr
from app_test import text_gen
from util import uuid, merge_dialog_in_and_out, translate_ns
from http.cookies import SimpleCookie
from util_mongo import (
    enqueue,
    dequeue,
    get_sorted_by_key,
)
from common import MONGODB_NAME, VALUE, KEY, IO_PREFIX
import pymongo as pm

# 连接Mongodb
mongo = pm.MongoClient('127.0.0.1', 27017, serverSelectionTimeoutMS=3000)
mdb = mongo[MONGODB_NAME]


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

    log = update_chat_history(username)

    return username, username, username, log


def chat_once(username, xinput):
    if username is None:
        return []
    ts = time.time_ns()
    enqueue(mdb, 'dialog_in', username, ts, {
        VALUE: xinput,
        'io': 'i',
    })
    xoutput = text_gen(xinput)
    ts = time.time_ns()
    enqueue(mdb, 'dialog_out', username, ts, {
        VALUE: xoutput,
        'io': 'o',
    })
    log = update_chat_history(username)
    return log


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
            text = row[VALUE]
            timestamp = row[KEY]
            dt_str = translate_ns(timestamp)
            xstr = IO_PREFIX.get(row["io"], '?') + ': '
            xstr += f'[ {dt_str} ] '

            xstr += text

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

    return log

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

    # 聊天历史
    cmp_chatbot = gr.Chatbot().style(height=350)

    # 输入控件
    xinput = gr.Textbox(interactive=True, label='输入')
    xinput_button = gr.Button('发送')

    # 按钮点击事件
    xinput_button.click(chat_once, [cmp_username_state, xinput], cmp_chatbot)

    # 加载时获取或设置cookie
    demo.load(embed_user_id_in_state_comp, None, [
        cmp_username_state,
        cmp_username_display,
        cmp_username_html,
        cmp_chatbot,
    ])
    # cmp_username_html发生变化时，触发JS，把生成的username放入页面cookie
    cmp_username_html.change(None, None, None, _js=js_username2cookie, queue=False)

# 用gradio启动，但是这样queue就不正常，可能还是得用uvicorn启动
# demo.launch(server_name='0.0.0.0', server_port=7776, share=True, debug=True)
demo.launch(server_name='0.0.0.0', server_port=7776, debug=True)
