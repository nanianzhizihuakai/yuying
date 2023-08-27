"""

TTS播放就比较复杂了。
由下面两个事件完成：
    cmp_start_btn.click(play_audio, [cmp_username_state, ], cmp_play_audio, every=0.1, )
    cmp_play_audio.change(None, None, None, _js=js_code, queue=False)
cmp_play_audio.change里面三个None是必须的，虽然会触发JS错误，但是只有这样才能保证每次cmp_play_audio更新后触发_js=js_code。
这里的js_code逻辑也是比较复杂。简单说就是，audio数据用base64组装成html audio元素放入cmp_play_audio里面，触发js_code，
把它append到cmp_play_audio_room。第一个数据由程序播放。后续数据由前面数据的onend事件触发播放。如果某数据播放后，后面没有数据了。
程序会播放下面的数据。数据播放后会自动清除。
（一定要清除，不然gradio页面存放大量audio数据会把用户的内存耗尽）

"""
import base64
import time
import gradio as gr
from app_test import text_gen
from util import uuid, merge_dialog_in_and_out, translate_ns, compose_wav_header
from http.cookies import SimpleCookie
from util_mongo import (
    enqueue,
    dequeue,
    get_sorted_by_key,
)
from common import MONGODB_NAME, VALUE, KEY, IO_PREFIX, RATE
import pymongo as pm
import redis
from tts_ws_python3_demo_mod import XunfeiTts

# 连接Mongodb
mongo = pm.MongoClient('127.0.0.1', 27017, serverSelectionTimeoutMS=3000)
mdb = mongo[MONGODB_NAME]
# 连接redis
rdb = redis.Redis('127.0.0.1', 6379, 0)


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
        print('username:', username)
        username = username.value
    except Exception:
        try:
            username = request.cookies['username']
        except Exception:
            pass

    # 获取不到，新建一个username
    if username is None:
        print('new username!')
        username = f'u{xuuid}'

    # print username
    print('username:', username)

    log = update_chat_history(username)

    return username, username, username, log


def chat_once(username, xinput):
    if username is None:
        return []

    # 输入存历史
    ts = time.time_ns()
    enqueue(mdb, 'dialog_in', username, ts, {
        VALUE: xinput,
        'io': 'i',
    })

    # 推理
    xoutput = text_gen(xinput, xusername=username)

    # 输出存历史
    ts = time.time_ns()
    enqueue(mdb, 'dialog_out', username, ts, {
        VALUE: xoutput,
        'io': 'o',
    })

    # 输出转语音
    # ttsObj = XunfeiTts(username, rdb, 'audio_stream_' + username)
    # ttsObj.tts(xoutput)

    # 获取历史
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


def play_audio(username):
    """
    播放声音
    :param username: 用户名
    :return: audio HTML element
    """
    if username is None:
        return ''

    audio = rdb.rpop('audio_stream_' + username)
    if audio is None:
        return ''

    # 加wave头
    xlen = len(audio)
    header = compose_wav_header(xlen, 1, 16, RATE)
    wav = header + audio

    # base64编码
    wav_b64 = base64.b64encode(wav).decode('ascii')
    html = f'<audio src="data:audio/wav;base64,{wav_b64}" controls></audio>'

    return html


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

# TTS播放配套的JS
js_code = """
    async () => {{
            setTimeout(function(){

                // new audio
                var xnew = document.querySelector('#audio_out.prose').innerHTML;
                if ('' == xnew) {
                    return;
                }
                window.audio_id = window.audio_id || 0;
                window.audio_id += 1;
                console.log(audio_id, new Date(), 'xnew', xnew.length)

                // append
                var room = document.querySelector('#audio_room.prose');
                var div = document.createElement('div');
                div.id = 'my_audio_' + audio_id;
                room.append(div);
                console.log(audio_id, new Date(), 'appended');

                // start ened event and trigger playing if needed
                div.innerHTML = xnew;
                var xnew_audio = div.querySelector('audio')
                if (!xnew_audio) {
                    console.log(audio_id, new Date(), 'new audio in div not found');
                    return;
                }
                xnew_audio.addEventListener('ended', function(){
                    var _this = this;

                    // remove this
                    setTimeout(function(){
                        _this.remove();
                        console.log(audio_id, new Date(), 'removed')
                    }, 100);
                    console.log(audio_id, new Date(), 'register this.remove');

                    // play next
                    var slot_after = div.nextElementSibling;
                    if (!slot_after) {
                        console.log(audio_id, new Date(), 'no slot_after');
                        window.is_need_manual = true;
                        return;
                    }
                    var next_audio = slot_after.querySelector('audio');
                    if (!next_audio) {
                        console.log(audio_id, new Date(), 'no next_audio');
                        window.is_need_manual = true;
                        return;
                    }
                    window.is_need_manual = false;
                    console.log(audio_id, new Date(), 'play next_audio');
                    next_audio.play();

                }, false);
                console.log(audio_id, new Date(), 'ended event registered');

                if (1 == audio_id || window.is_need_manual) {
                    console.log(audio_id, new Date(), 'manually play');
                    window.is_need_manual = false;
                    xnew_audio.play();
                }

            }, 1);
        }}
"""


def do_the_init():
    """
        点击”开始聊天“的事件的handler
        :return: 隐藏”开始聊天“，显示其他组件。
    """
    return (
        gr.update(visible=False),
        *([gr.update(visible=True)] * 3),
    )


with gr.Blocks(analytics_enabled=False) as demo:

    # 用户名
    cmp_username_state = gr.State()
    cmp_username_html = gr.HTML(visible=False, elem_id='username')
    cmp_username_display = gr.Textbox(interactive=False, label='用户名')

    # 启动按钮
    cmp_start_btn = gr.Button('开始聊天')

    # 聊天历史
    cmp_chatbot = gr.Chatbot(visible=False).style(height=350)

    # 输入控件
    xinput = gr.Textbox(interactive=True, label='输入', visible=False)
    xinput_button = gr.Button('发送', visible=False)

    # 语音播放
    cmp_play_audio = gr.HTML(elem_id='audio_out')
    # cmp_play_audio.visible = False
    cmp_play_audio_room = gr.HTML(elem_id='audio_room')
    # cmp_play_audio_room.visible = False

    # 按钮点击事件
    xinput_button.click(chat_once, [cmp_username_state, xinput], cmp_chatbot, queue=False)

    # 加载时获取或设置cookie
    demo.load(embed_user_id_in_state_comp, None, [
        cmp_username_state,
        cmp_username_display,
        cmp_username_html,
        cmp_chatbot,
    ])
    # cmp_username_html发生变化时，触发JS，把生成的username放入页面cookie
    cmp_username_html.change(None, None, None, _js=js_username2cookie, queue=False)

    # audio output
    cmp_start_btn.click(play_audio, cmp_username_state, cmp_play_audio, every=0.1, )
    cmp_play_audio.change(None, None, None, _js=js_code, queue=False)

    # 启动
    cmp_start_btn.click(do_the_init, None, [
        cmp_start_btn,
        cmp_chatbot,
        xinput,
        xinput_button,
    ], queue=False)

# 使用queue
demo.queue(
    concurrency_count=100,
    status_update_rate='auto',
    # status_update_rate=0.02,
)

# 用gradio启动，但是这样queue就不正常，可能还是得用uvicorn启动
# demo.launch(server_name='0.0.0.0', server_port=6006, share=True, debug=True)
demo.launch(server_name='0.0.0.0', server_port=6006, debug=True)
