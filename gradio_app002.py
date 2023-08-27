import gradio as gr
from app_test import text_gen

# def greet(name):
#     return "Hello, " + name + "!"

iface = gr.Interface(fn=text_gen, inputs="text", outputs="text")
iface.launch(share=True)
