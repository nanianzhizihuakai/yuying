import gradio as gr
from app_test import text_gen

iface = gr.Interface(fn=text_gen, inputs="text", outputs="text")
# iface.launch()
iface.launch(share=True)  # To create a public link, set `share=True` in `launch()`.
