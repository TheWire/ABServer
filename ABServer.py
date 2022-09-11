import machine
import network
import socket
import os
import uasyncio
import re

MIME_TYPES = {
    '.html': 'text/html',
    '.htm': 'text/html',
    '.css': 'text/css',
    '.js': 'text/javascript',
    '.json': 'application/json',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.gz': 'application/gzip',
    '.csv': 'text/csv',
    '.bmp': 'image/bmp',
    '.png': 'image/png',
    '.pdf': 'application/pdf',
    '.sh': 'application/x-sh',
    '.svg': 'image/svg+xml',
    '.txt': 'text/plain',
    '.ttf': 'font/ttf',
    '.wav': 'audio/wav',
    '.weba': 'audio/webm',
    '.webm': 'video/webm',
    '.webp': 'image/webp',
    '.xhtml': 'application/xhtml+xml',
    '.xml': 'application/xml',
    '.zip': 'application/zip',
    '.ts': 'video/mp2t',
    '.tif': 'image/tiff',
    '.tiff': 'image/tiff',
    '.otf': 'font/otf',
    '.aac': 'audio/aac',
    '.rtf': 'application/rtf',
    '.avi': 'video/x-msvideo',
    '.bz': 'application/x-bzip',
    '.bz2': 'application/x-bzip2',
    '.ico': 'image/vnd.microsoft.icon',
    '.mid': 'audio/midi',
    '.midi': 'audio/x-midi',
    '.bz': 'application/x-bzip',
    '.bz2': 'application/x-bzip2',
    '.mp3': 'audio/mpeg',
    '.mp4': 'video/mp4',
    '.mpeg': 'video/mpeg',
    
}

class Server:
    
    def __init__(self, network):
        
        
        self.network = network
        self.middlewares = []
        
        self.__regex_type = type(re.compile(""))
        
    def __route_middleware(self, route, middleware):
        if type(route) is self.__regex_type:
            re_route = route
        else:
            re_route = self.__get_re_route(route.lower())
        async def route_middleware(request, response):
            if self.__match_route(re_route, request.route):
                await self.__call_middleware(middleware)(request, response)
        return route_middleware
    
    def __get_re_route(self, route):
        __route = route

        if __route[-1] == '/' and len(__route) > 1:
            __route += '[A-Za-z0-9_.,%$£-]+'
        else :
            __route += '/?'
        return re.compile(__route)
    
    def __match_route(self, re_route, request_route):
        match = re_route.search(request_route)
        if not match: return False
        return len(request_route) == len(match.group(0))
    
    def use(self, *args):
        if type(args[0]) is str or type(args[0]) is self.__regex_type:
            for middleware in args[1:]:
                self.middlewares.append(self.__route_middleware(args[0], middleware))
        else:
            for middleware in args:
                self.middlewares.append(self.__call_middleware(middleware))
    
    def __call_middleware(self, middleware):
        async def async_middleware(request, response):
            if iscoroutine(middleware(request, response)):
                await middleware(request, response)
        return async_middleware
            
            
        if iscoroutine(middleware):
            return async_middleware
        else:
            return sync_middleware
        
        
        
    def __method_middleware(self, method, middleware):
        async def method_middleware(request, response):
            if(request.method == method):
                await middleware(request, response)
        return method_middleware
    
    def get(self, route, middleware):
        route_middleware = self.__route_middleware(route, middleware)
        method_middleware = self.__method_middleware('GET', route_middleware)
        self.middlewares.append(method_middleware)
        
    def post(self, route, middleware):
        route_middleware = self.__route_middleware(route, middleware)
        method_middleware = self.__method_middleware('POST', route_middleware)
        self.middlewares.append(method_middleware)
        
    def put(self, route, middleware):
        route_middleware = self.__route_middleware(route, middleware)
        method_middleware = self.__method_middleware('PUT', route_middleware)
        self.middlewares.append(method_middleware)
        
    def delete(self, route, middleware):
        route_middleware = self.__route_middleware(route, middleware)
        method_middleware = self.__method_middleware('DELETE', route_middleware)
        self.middlewares.append(method_middleware)
        
    def patch(self, route, middleware):
        route_middleware = self.__route_middleware(route, middleware)
        method_middleware = self.__method_middleware('PATCH', route_middleware)
        self.middlewares.append(method_middleware)
        
    def head(self, route, middleware):
        route_middleware = self.__route_middleware(route, middleware)
        method_middleware = self.__method_middleware('HEAD', route_middleware)
        self.middlewares.append(method_middleware)
        
    async def listen(self, ip='0.0.0.0', port=80):
        if not self.network.isconnected():
            raise NetworkError("network not connected")
        self.ip = ip
        self.port = port
        await self.__listen(ip, port)
        
    def static(self, static_file_path):
        def __static (request, response):
            if(request.method == 'GET'):
                file_name = re.search('[A-Za-z0-9_.,%$£-]+$', request.route).group(0)
                sanitized_path = file_name.replace('..', '')
                try:
                    os.chdir(static_file_path)
                    files = os.listdir()
                    if sanitized_path in files:
                        file = open(sanitized_path)
                        response.set_header('Content-Type', self.__get_mime(sanitized_path))
                        response.send(file.read())
                        file.close()
                    os.chdir('..')
                except OSError as e:
                    if e.args[0] == -2:
                        raise FilePathError("Cannot find static file path")
                    else:
                        raise e
        
        return __static
    
    def __get_mime(self, file_name):
        extension_match = re.search('.[A-Za-z0-9]+$', file_name)
        if extension_match is not None:
            extension = extension_match.group(0).lower()
            if extension in MIME_TYPES:
                return MIME_TYPES[extension]
            else:
                return 'text/html'
            
    def __exception_handler(self, loop, context):
        print("exception")
        if context["exception"] is uasyncio.CancelledError:
            print("stopping server")
            loop.close()
        else:
            ex = context["exception"]

                    
                       
    async def __listen(self, ip, port):
        self.__address = socket.getaddrinfo(ip, port)[0][-1]
#         uasyncio.Loop.set_exception_handler(self.__exception_handler)
        self.__server = await uasyncio.start_server(self.__handle_request, host = ip, port = port)
        while True:
            await uasyncio.sleep(1.0)
        
    
    async def __handle_request(self, reader, writer):
        request = await reader.read(4096)
        if request is None or request == b'':
            writer.close()
            await writer.wait_closed()
            return
        
        requestObj = Request(request)
        responseObj = Response(writer)
        for middleware in self.middlewares:
            await middleware(requestObj, responseObj)
            
        if not responseObj.__has_responded:
                responseObj.status('404 Not Found')
                responseObj.send('404 Not Found')
        await responseObj.close()  
            
class Response:
    def __init__(self, writer):
        self.writer = writer
        self.__version = 'HTTP/1.1'
        self.__status = '200 OK'
        self.__headers = {
            'X-Powered-By': ('AB-Server', False),
            'Content-Type': ('text/html', False)
        }
        self.__start_response = False
        self.__headers_sent = False
        self.__has_responded = False
                                                
    def set_header(self, key, value):
        self.__send_header(key, value)
        
    def status(self, status):
        self.__status = status
        
    def set(self, headers):
        for key, value in headers.items():
            self.__send_header(key, value)
            
    def __send_header(self, key, value):
        if key in self.__headers and self.__headers[key][1]:
            raise AlreadyRespondedError("Already sent header")
        self.__headers[key] = (value, True)
        header = key + ': ' + value + "\r\n"
        self.__http_write(header)
            
    def __send_headers(self):
        if self.__headers_sent:
            raise AlreadyRespondedError("Already sent headers")
        for key, value in self.__headers.items():
            if not value[1]:
                self.__send_header(key, value[0])
        self.__http_write("\r\n")
        self.__headers_sent = True
        
    def send(self, content):
        self.write(content)
        self.end()
        
    def write(self, content):
        if not self.__headers_sent:
            self.__send_headers()
        self.__http_write(content)
        
    def end(self, content=""):
        self.write(content)
        self.write("\r\n")
        self.__has_responded = True       
    
    async def close(self):
        await self.writer.drain()
        self.writer.close()
        await self.writer.wait_closed()
        
    def __http_start_response(self):
        if not self.__start_response:
            self.__write(' '.join([self.__version, self.__status]) + "\r\n")
            self.__start_response = True
        
    def __http_write(self, data):
        self.__http_start_response()
        self.__write(data)
        
    def __write(self, data):
        if self.__has_responded:
            raise AlreadyRespondedError("Already responded to this request")
        self.writer.write(data)
    
    
class Request:
    def __init__(self, request):
        self.request = request.decode()
        self.__pass_request()
    
    def __pass_request(self):
        request_parts = self.request.splitlines()[0].split(' ')
        if len(request_parts) < 2: raise InvalidRequestError("invalid http request")
        self.method = request_parts[0]
        self.route = request_parts[1].lower()
           
            
        
class ABServerError(Exception):
    pass

class NetworkError(ABServerError):
    pass

class InvalidRequestError (ABServerError):
    pass

class AlreadyRespondedError(ABServerError):
    pass

class FilePathError(ABServerError):
    pass


#helper functions

#good enough to identify awaitable function
def iscoroutine(obj):
    return hasattr(obj, "send")