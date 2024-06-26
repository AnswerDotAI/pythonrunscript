#!/usr/bin/env pythonrunscript

# ```requirements.txt
# python-fasthtml>=0.0.16
# uvicorn>=0.29
# python-multipart
# ```

from fasthtml.fastapp import *
from fastcore.utils import *

app = fast_app(hdrs=[HighlightJS()])
rt = app.route

@rt("/convert")
def post(html: str): return Pre(Code(html2xt(html))) if html else ''

@rt("/")
def get():
    txt = Textarea(id="html", rows=10, hx_post='/convert', target_id="xt", hx_trigger='keyup delay:500ms'),
    return Titled("Convert HTML to XT",
                  Label("HTML"), txt, Div(id="xt"))

if __name__ == '__main__': uvicorn.run("main:app", host='0.0.0.0', port=int(os.getenv("PORT", default=5000)))

