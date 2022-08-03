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
    
    def __init__(self, network, break_pin=None):
        
        
        self.network = network
        self.middlewares = []
        if not network.isconnected():
            raise NetworkError("network not connected")
        
        self.__set_break_button(break_pin)
        
        self.__regex_type = type(re.compile(""))
    
    def __set_break_button(self, pin):
        if pin is not None:
            self.__break_button = machine.Pin(pin, machine.Pin.IN, machine.Pin.PULL_UP)
        else:
            self.__break_button = None
        
    def __route_middleware(self, route, middleware):
        if type(route) is self.__regex_type:
            re_route = route
        else:
            re_route = self.__get_re_route(route.lower())
        def route_middleware(request, response):
            if self.__match_route(re_route, request.route):
                middleware(request, response)
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
        return len(request_route) == match.span()[1] - match.span()[0]
    
    def use(self, *args):
        if type(args[0]) is str or type(args[0]) is self.__regex_type:
            for middleware in args[1:]:
                self.middlewares.append(self.__route_middleware(args[0], middleware))
        else:
            for middlware in args:
                self.middlewares.append(middleware)
    
        
    def __method_middleware(self, method, middleware):
        def method_middleware(request, response):
            if(request.method == method):
                middleware(request, response)
        return method_middleware
    
    def get(self, route, middleware):
        route_middleware = self.__route_middleware(route, middleware)
        method_middleware = self.__method_middleware('GET', route_middleware)
        self.middlewares.append(method_middleware)
        
    def post(self, route, middleware):
        route_middlware = self.__route_middlware(route, middleware)
        method_middleware = self.__method_middleware('POST', route_middlware)
        self.middlewares.append(method_middleware)
        
    def listen(self, ip='0.0.0.0', port=80):
        self.ip = ip
        self.port = port
        self.__listen(ip, port)
        
    def static(self, static_file_path):
        def __static (request, response):
            if(request.method == 'GET'):
                file_span = re.search('[A-Za-z0-9_.,%$£-]+$', request.route).span()
                file_name = request.route[file_span[0]:file_span[1]]
                sanitized_path = file_name.replace('..', '')
                os.chdir(static_file_path)
                files = os.listdir()
                if sanitized_path in files:
                    file = open(sanitized_path)
                    response.set_header('Content-type', self.__get_mime(sanitized_path))
                    response.send(file.read())
                os.chdir('..')
        
        return __static
    
    def __get_mime(self, file_name):
        extension_match = re.search('.[A-Za-z0-9]+$', file_name)
        if extension_match is not None:
            span = extension_match.span()
            extension = file_name[span[0]:span[1]].lower()
            if extension in MIME_TYPES:
                return MIME_TYPES[extension]
            else:
                return 'text/html'
        
                    
                       
    def __listen(self, ip, port):
        self.__address = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
        self.__socket = socket.socket()
        self.__socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.__socket.bind(self.__address)
        self.__socket.listen(1)
        while True:
            self.__handle_requests()
            if self.__break_button is not None and self.__break_button.value() == 0:
                break
        
            
    def __handle_requests(self):
        client, address = self.__socket.accept()
        request = client.recv(1024)
        self.__handle_request(client, request)
    
    def __handle_request(self, client, request):
        if request == b'': client.close(); return
        requestObj = Request(request)
        responseObj = Response(client)
        for middleware in self.middlewares:
            middleware(requestObj, responseObj)
            
        if not responseObj.has_responded:
                responseObj.send('404 Not Found')
                
            
class Response:
    def __init__(self, client):
        self.client = client
        self.version = 'HTTP/1.0'
        self.status = '200 OK'
        self.headers = {
            'Content-type': 'text/html'
        }
        self.has_responded = False
                                                
    def set_header(self, key, value):
        self.headers[key] = value
        
    def send(self, content):
        if(self.has_responded): raise AlreadyRespondedError("Already responded to this request")
        self.client.send(self.__response_str(content))
        self.has_responded = True
        self.client.close()
        
    def __response_str(self, content):
        strList = [' '.join([self.version,self.status])]
        for key, value in self.headers.items():
            strList.append(key + ': ' + value)
        strList.append('') # empty line after headers
        strList.append(content)
        return '\r\n'.join(strList) + '\r\n'
    
class Request:
    def __init__(self, request):
        self.request = request.decode()
        self.__pass_request()
    
    def __pass_request(self):
        request_line = self.request.splitlines()[0].split(' ')
        self.method = request_line[0]
        self.route = request_line[1].lower()
           
            
        
class ABServerError(Exception):
    pass

class NetworkError(ABServerError):
    pass

class AlreadyRespondedError(ABServerError):
    pass