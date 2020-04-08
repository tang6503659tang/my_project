import logging; logging.basicConfig(level=logging.INFO)

import asyncio,os,json,time
from datetime import datetime
from aiohttp import web

async def index(request):
    return web.Response(body=b'<h1> Hello, my friends!</h1>',content_type="text/html")

def init():
    app=web.Application()
    app.add_routes([web.get('/',index)])
    logging.info("Server started at 127.0.0.1...")
    web.run_app(app,host='127.0.0.1',port=8080)

init()