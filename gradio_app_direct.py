import gradio as gr
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks

text_generation_zh_dict = pipeline(Tasks.text_generation, model='damo/nlp_gpt3_text-generation_chinese-base')
print('--------------------热身运动---------------------------------------')
text_generation_zh_dict('热身运动')
print('--------------------ALL IS READY---------------------------------------')


def text_generation_zh(xinput):
    print('<<<<', xinput)
    xdict = text_generation_zh_dict(xinput)
    xoutput = xdict['text']
    print('>>>>', xoutput)
    return xoutput


iface = gr.Interface(fn=text_generation_zh, inputs="text", outputs="text")
# iface.launch()
iface.launch(share=True)  # To create a public link, set `share=True` in `launch()`.
