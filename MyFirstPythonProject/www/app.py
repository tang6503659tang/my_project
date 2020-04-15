import logging;logging.basicConfig(level=logging.INFO)

import asyncio,os,json,time
from datetime import datetime
from aiohttp import web
from jinja2 import Environment,FileSystemLoader
from www import orm
from www.coroweb import add_routes

async def index(request):
    return web.Response(body=b'<h1> Hello, my friends!</h1>',content_type="text/html")

async def init(loop):
        await orm.create_pool(loop,host='127.0.0.1',port=3306,user='www-data',password='www-data',ab='web_practice')
        app=web.Application(loop=loop,middlewares=[logger_factory,response_factory])
        init_jinja2(app,filters=dict(datetime=datetime_filter))
        add_routes(app,'handler')
        logging.info("Server started at 127.0.0.1...")
        web.run_app(app,host='127.0.0.1',port= 8080)


def init_jinja2(app,**kw):
    '''
    initializing jinja framework
    :param app:
    :param kw:
    :return:
    '''
    logging.info("init jinjia2...")
    options = dict(
        block_start_string=kw.get("block_start_string",'{%'),
        autoescape = kw.get('autoescape',True),
        block_end_string = kw.get('block_end_string','%}'),
        variable_start_string = kw.get('variable_start_string','{{'),
        variable_end_string = kw.get('variable_end_string','}}'),
        auto_reload = kw.get('auto_reload',True)
    )
    path = kw.get('path',None)
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'templates')
    logging.info('set jinja2 template path: %s' % path)
    env = Environment(loader=FileSystemLoader(path),**options)
    filters = kw.get('filters',None)
    if filters is not None:
        for name,f in filters.items():
            env.filters[name]=f
    app["__tmeplating__"]=env

async  def logger_factory(app,handler):
    async def logger(request):
        logging.info('Request: %s %s' % (request.method,request.path))
        return (await handler(request))
    return logger

async def data_factory(app,handler):
    async def parse_data(request):
        if request.method == "post":
            if request.content_type.startswith('application/json'):
                request.__data__= await request.json()
                logging.info('request json: %s' % str(request.__data__))
            elif request.content_type.startswith('application/x-www-form-urlencoded'):
                request.__data__=await request.post()
                logging.info('request form: %s' % str(request.__data__))
        return (await handler(request))
    return parse_data

async def response_factory(app,handler):
    async def response(request):
        logging.info('Response handler...')
        r=handler(request)
        if isinstance(r,web.StreamResponse):
            return r
        if isinstance(r,bytes):
            resp=web.Response(body=r)
            resp.content_type='application/octet-stream'
            return resp
        if isinstance(r,str):
            if r.startswith('redirect:'):
                return web.HTTPFound(r[9:])
            resp = web.Response(body=r.encode('utf-8'))
            resp.content_type='text/html;charset=utf-8'
            return resp
        if isinstance(r,dict):
            template=r.get('__template__')
            if template is None:
                resp = web.Response(body=json.dumps(r,ensure_ascii=False,default=lambda o:o.__dict__).encode("utf-8"))
                resp.content_type='application/json;charset=utf-8'
                return resp
            else:
                resp = web.Response(body=app['__template__'].get_template(template).render(**r).encode("utf-8"))
                resp.content_type = 'text/html; charset=utf-8'
                return resp
        if isinstance(r,int) and r>=100 and r<=600:
            return web.Response(r)
        if isinstance(r,tuple) and len(r)==2:
            t,m=r
            if isinstance(t,int) and t>=100 and t<=600:
                return web.Response(t,str(m))
        resp = web.Response(body=str(r).encode('utf-8'))
        resp.content_type = 'text/plain;charset=utf-8'
        return resp
    return response


def datetime_filter(t):
    delta = int(time.time()-t)
    if delta <60:
        return u"1分钟前"
    if delta <3600:
        return u"%s分钟前" % (delta//60)
    if delta <86400:
        return u'%s小时前' % (delta//3600)
    if delta <604800:
        return u'%s天前' % (delta//86400)
    dt = datetime.fromtimestamp(t)
    return u'%s年%s月%s日' % (dt.year,dt.month,dt.day)



