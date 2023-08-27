import gradio as gr
from app_test import text_gen
from util import uuid
from http.cookies import SimpleCookie


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

    return username, username, username


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

    # 输入输出控件
    xinput = gr.Textbox(interactive=True, label='输入')
    xinput_button = gr.Button('发送')
    xoutput = gr.Textbox(interactive=False, label='输出')

    # 按钮点击事件
    xinput_button.click(text_gen, xinput, xoutput)

    # 加载时获取或设置cookie
    demo.load(embed_user_id_in_state_comp, None, [
        cmp_username_state,
        cmp_username_display,
        cmp_username_html
    ])
    # cmp_username_html发生变化时，触发JS，把生成的username放入页面cookie
    cmp_username_html.change(None, None, None, _js=js_username2cookie, queue=False)  # hack

# 用gradio启动，但是这样queue就不正常，可能还是得用uvicorn启动
demo.launch(server_name='0.0.0.0', server_port=7776, share=True, debug=True)
