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

def add_static(app):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    app.router.add_static('/static/', path)
    logging.info('add static %s => %s' % ('/static/', path))

def get_required_kw_args(fn):
    args=[]
    parms=inspect.signature(fn).parameters #return the input parameters of a callable object
    for name,parm in parms.items():
        if parm.kind == inspect.Parameter.KEYWORD_ONLY and parm.default == inspect.Parameter.empty:
            args.append(name) #return input that needed to fill and not positional
    return tuple(args)

def get_named_kw_args(fn):
    args=[]
    params = inspect.signature(fn).parameters
    for name,param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            args.append(name)   #return input that has keyword but not postitional
    return tuple(args)

def has_named_kw_arg(fn):
    params = inspect.signature(fn).parameters
    for param in params.values():
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            return True
def has_var_kw_arg(fn):
    params = inspect.signature(fn).parameters
    for param in params.values():
        if param.kind == inspect.Parameter.VAR_KEYWORD: # **kw
            return True

def has_request_arg(fn):
    sig=inspect.signature(fn)
    params = sig.parameters
    found = False
    for name, param in params.items():
        if name == 'request':
            found=True
            continue
        if found and (param.kind != inspect.Parameter.VAR_KEYWORD and param.kind != inspect.Parameter.VAR_POSITIONAL
                      and param.kind != inspect.Parameter.KEYWORD_ONLY):
            raise ValueError('request parameter must be the last named parameter in function %s%s' % (fn.__name__,str(sig)))
    return found



class RequestHandler(object):
    '''
    using for handling request
    '''
    def __init__(self,app,fn):
        self._app=app
        self._func=fn
        self._required_kw_args=get_required_kw_args(fn)
        self._named_kw_args=get_named_kw_args(fn)
        self._has_named_kw_arg=has_named_kw_arg(fn)
        self._has_var_kw_arg=has_var_kw_arg(fn)
        self._has_request_arg=has_request_arg(fn)
    async def __call__(self, request):
        kw = None
        if self._has_var_kw_arg or self._has_named_kw_arg or self._has_request_arg:
            if request.method=='post':  # use post method
                if not request.content_type:
                    return web.HTTPBadRequest("Missing Content-Type!") # data form
                ct=request.content_type.lower()
                if ct.startswith('application/json'):
                    params = await request.json()
                    if not isinstance(params,dict):
                        return web.HTTPBadRequest("JSON body must be object!")
                    kw = params
                elif ct.startswith('application/x-www-form-urlencoded') or ct.startswith('multipart/form-data'):
                    params = await request.post()
                    kw = dict(**params)
                else:
                    return web.HTTPBadRequest("Unsupported Content-Type: %s" % request.content_type)
            if request.method == 'get':
                qs = request.query_string
                if qs:
                    kw=dict()
                    for k,v in parse.parse_qs(qs,True).items():
                        kw[k] = v[0]
            if kw is None:
                kw=dict(**request.match_info)
            else:
                if not self._has_var_kw_arg and self._has_named_kw_arg:
                    copy = dict()
                    for name in self._named_kw_args:
                        if name in kw:
                             copy[name]=kw[name]
                    kw=copy # remove all unnamed kw

                # check named arg
                for k,v in request.match_info.items():
                    if k in kw:
                        logging.warning('Duplicate arg name in named args and kw args: %s' % k)
                    kw[k]=v
            if self._has_request_arg:
                kw['request']=request
            if self._required_kw_args:
                for name in self._required_kw_args:
                    if not name in kw:
                        return web.HTTPBadRequest("Missing argument: %s" % name)
            logging.info('Call with args: %s' % str(kw))
            try:
                r = await self._func(**kw)
            except APIError as e:
                return dict(error=e.error,data=e.data,message=e.message)

