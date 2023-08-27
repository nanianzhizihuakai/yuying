import gradio as gr
from app_test import text_gen

with gr.Blocks(analytics_enabled=False) as demo:
    xinput = gr.Textbox(interactive=True, label='输入')
    xinput_button = gr.Button('发送')
    xoutput = gr.Textbox(interactive=False, label='输出')

    xinput_button.click(text_gen, xinput, xoutput)

# 用gradio启动，但是这样queue就不正常，可能还是得用uvicorn启动
demo.launch(server_name='0.0.0.0', server_port=7776, share=True, debug=True)
