import asyncio,logging,inspect,os,functools
from urllib import parse
from aiohttp import web
from www.apis import APIError

'''
design decorators that can pass parameters
'''
def get(path):
    '''
    define decorator @get('/path')
    :param path:
    :return:decorator
    '''
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args,**kw):
            return func(*args,**kw)
        wrapper.__method__='GET'
        wrapper.__route__=path
        return wrapper
    return decorator
def post(path):
    '''
    define decorator @post('/path')
    :param path:
    :return:
    '''
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args,**kw):
            return func(*args,**kw)
        wrapper.__method__='POST'
        wrapper.__route__=path
        return wrapper
    return decorator

def add_route(app,fn):# url analyzing
    method=getattr(fn,'__method__',None)
    path=getattr(fn,'__route__',None)
    if path is None or method is None:
        raise ValueError('@get or @post not defined in %s' % str(fn))
    if not asyncio.iscoroutinefunction(fn) and not inspect.isgeneratorfunction(fn):
        fn=asyncio.coroutine(fn) # coroutine
    logging.info('add route %s %s => %s(%s)' % (method,path,fn.__name__,','.join(inspect.signature(fn).parameters.keys())))
    app.router.add_route(method,path,RequestHandler(app,fn))

def add_routes(app,module_name):# auto-scanning for add_route
    n = module_name.rfind('.')
    if n==(-1):
        mod=__import__(module_name,globals(),locals()) # dynamic loading
    else:
        name=module_name[n+1:]
        mod=getattr(__import__(module_name[:n],globals(),locals(),[name]),name)
    for attr in dir(mod):
        if attr.startswith('_'): # skipping the private method
            continue
        fn=getattr(mod,attr)
        if callable(fn):
            method = getattr(fn,'__method__',None)
            path = getattr(fn,'__route__',None)
            if method and path:
                add_route(app,fn)


class RequestHandler(object):
    '''
    using for handling request
    '''
    def __index__(self,app,fn):
        self.app=app
        self.fn=fn
    @asyncio.coroutine
    def __call__(self,request):
        kw=...
        r= yield from self._func(**kw)
        return r
