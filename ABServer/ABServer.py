import os
try:
    os.uname().sysname
    import uasyncio as asyncio
except:
    import asyncio
import socket
import re
import json
import gc

MIME_TYPES = {
    'html': 'text/html', 'htm': 'text/html', 'css': 'text/css', 'js': 'text/javascript',
    'json': 'application/json', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'gif': 'image/gif',
    'gz': 'application/gzip', 'csv': 'text/csv', 'bmp': 'image/bmp', 'png': 'image/png',
    'pdf': 'application/pdf', 'sh': 'application/x-sh', 'svg': 'image/svg+xml', 'txt': 'text/plain',
    'ttf': 'font/ttf', 'wav': 'audio/wav', 'weba': 'audio/webm', 'webm': 'video/webm', 'webp': 'image/webp',
    'xhtml': 'application/xhtml+xml', 'xml': 'application/xml', 'zip': 'application/zip', 'ts': 'video/mp2t',
    'tif': 'image/tiff', 'tiff': 'image/tiff', 'otf': 'font/otf', 'aac': 'audio/aac', 'rtf': 'application/rtf',
    'avi': 'video/x-msvideo', 'bz': 'application/x-bzip', 'bz2': 'application/x-bzip2', 'ico': 'image/vnd.microsoft.icon',
    'mid': 'audio/midi', 'midi': 'audio/x-midi', 'bz': 'application/x-bzip', 'bz2': 'application/x-bzip2',
    'mp3': 'audio/mpeg', 'mp4': 'video/mp4', 'mpeg': 'video/mpeg',
}

class ABServerError(Exception):
    pass

class NetworkError(ABServerError):
    pass

class InvalidRequestError(ABServerError):
    pass

class AlreadyRespondedError(ABServerError):
    pass

class FilePathError(ABServerError):
    pass

class Comp_File_Policy:
    NO_COMP = 1
    GZ_COMP = 2
    ALL_COMP = 3

class Server:
    
    def __init__(self):
        
        
        self.middlewares = []
        
        # self.__regex_type = type(re.compile(""))
        self.__server = None
        
    def __route_middleware(self, route, middleware, complete_match=True):
        route = self.__get_path_parser(route.lower())
        async def route_middleware(request, response):
            ret = self.__match_route(route, request.url_parts, complete_match)
            if ret != False:
                request.params = ret
                await self.__call_middleware(middleware)(request, response)
        return route_middleware

    def __get_path_parser(self, path):
        parts = path.split("/")
        path_parser = []
        for part in parts:
            if part == "": continue
            params = part.split(":")
            if len(params) == 1:
                path_parser.append(params[0])
                continue
                
            param_block = {"path":"", "params": []}
            if params[0] != "":
                param_block["path"] = params[0]
            for param in params[1:]:
                param_block["params"].append(param)
            path_parser.append(param_block)
        return path_parser

    
    def __match_route(self, url_parser, request_path, complete_match=True):
        pos = 0
        params = {}
        if len(url_parser) != len(request_path) and complete_match: return False
        for part in url_parser:
            if pos >= len(request_path): return False
            if type(part) == dict:
                ret = self.__parse_params(part, request_path[pos])
                if ret == False: return False
                params.update(ret)
            elif part != request_path[pos]:
                return False
            pos += 1
        return params
        
    def __parse_params(self, params, url_part):
        parsed_params = {}
        pos = 0
        if params["path"] != "":
            pos = url_part.find(params["path"])
            if pos != 0: return False
            pos = len(params["path"])
        for idx, param in enumerate(params["params"]):
            if pos == len(url_part): return False
            if idx == len(params["params"]) -1:
                parsed_params[param] = url_part[pos:]
            else:
                parsed_params[param] = url_part[pos]
            pos += 1
        return parsed_params
    
    def use(self, *args):
        if type(args[0]) is str:
            for middleware in args[1:]:
                self.middlewares.append(self.__route_middleware(args[0], middleware, False))
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
        if self.__server != None:
            raise ABServerError("server already started")

        self.ip = ip
        self.port = port
        await self.__listen(ip, port)

    async def stop(self):
        if self.__server == None:
            raise ABServerError("server not started")
        print("stopping server...")
        self.__server.close()
        await self.__server.wait_closed()
        self.__server = None
        print("server stopped")

    def static(self, static_file_path, compressed_file_policy=Comp_File_Policy.NO_COMP):
        def __static (request, response):
            if(request.method == 'GET'):
                #look at this again
                file_name = re.search('[A-Za-z0-9_.,%$£-]+$', request.route).group(0)
                sanitized_path = sanitize_path(file_name)
                joined_path = join_path(static_file_path, sanitized_path)
                final_path, compressed = get_file_to_send(joined_path, compressed_file_policy)
                if final_path is None:
                    response.status("404 Not Found")
                    response.end()
                if compressed: response.set_header('Content-Encoding', 'gzip')
                response.send_file(final_path, compressed_file_policy)
        return __static

    def __parse_contentType(self, header):
        contentType = header.split(';', 1)
        return contentType[0].strip(), contentType[1].strip() if len(contentType) == 2 else ""

    def json_body_parser(self):
        def __json(request, response):
            try: request.body
            except: request.body = {}
            if request.headers.get("content-type") == None: return
            contentType, _ = self.__parse_contentType(request.headers["content-type"])
            if contentType != MIME_TYPES["json"]: return
            try:
                request.body = json.loads(request.raw_body)
            except:
                pass
        return __json

    def url_encoded_body_parser(self):
        def __url_encoded(request, response):
            try: request.body
            except: request.body = {}
            request.body = {}
            if ("content-ype", "application/x-www-form-urlencoded") not in request.headers.items(): return
            request.body = parse_query(request.raw_body)
        return __url_encoded

    def cors(self):
        def __cors(request, response):
            response.set_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            response.set_header("Access-Control-Allow-Origin", "*")
            response.set_header("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept")
            if request.method == "OPTIONS":
                response.set_header("Access-Control-Allow-Origin","*")
                response.set_header("Access-Control-Allow-Methods","*")
                response.set_header("Access-Control-Allow-Credentials", "true")
                response.set_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
                response.end()
        return __cors
            
    def __exception_handler(self, loop, context):
        exception = context["exception"]
        if exception is asyncio.CancelledError:
            print("stopping server")
            loop.close()
        elif type(exception) is OSError and exception.errno == 104:
            print("socket closed")
        else:
            raise exception

                    
                       
    async def __listen(self, ip, port):
        self.__address = socket.getaddrinfo(ip, port)[0][-1]
        asyncio.get_event_loop().set_exception_handler(self.__exception_handler)
        self.__server = await asyncio.start_server(self.__handle_request, host = ip, port = port)
    
    async def __handle_request(self, reader, writer):
        gc.collect()
        request = await reader.read(4096)
        if request is None or request == b'':
            writer.close()
            await writer.wait_closed()
            return
        
        addr = writer.get_extra_info('peername')
        responseObj = Response(writer, addr)
        try:
            requestObj = Request(request, addr)
        except InvalidRequestError as e:
            responseObj.status('400 Bad Request')
            responseObj.end()

        for middleware in self.middlewares:
            await middleware(requestObj, responseObj)
            
        if not responseObj.has_responded:
                responseObj.status("404 Not Found")
                responseObj.end('404 Not Found')
        await responseObj.close()  
            
class Response:

    def __init__(self, writer, address):
        self.writer = writer
        self.__version = 'HTTP/1.1'
        self.__status = '200 OK'
        self.headers = {
            'X-Powered-By': 'AB-Server',
            'Content-Type': 'text/html'
        }
        self.address = address
        self.__start_response = False
        self.__headers_sent = False
        self.has_responded = False    

    def set_header(self, key, value):
        self.headers[key] = value

        
    def status(self, status):
        self.__status = status
        
    def set(self, headers):
        self.headers.update(headers)
            
    def __http_send_header(self, key, value):
        header = key + ': ' + value
        # self.__write(header.lower() if header is not None else "")
        self.__write(header)
        self.__write("\r\n")
            
    def __http_send_headers(self):
        if self.__headers_sent: return
        for key, value in self.headers.items():
            self.__http_send_header(key, value)
        self.__headers_sent = True
        self.__write("\r\n")
        
    def send(self, content):
        if ("Transfer-Encoding", "chunked") in self.headers.items():
            self.write(content)
        else:
            self.__http_write(content)
        self.end()


    def send_file(self, filepath, gz_as_compressed=False):
        extension, compressed = get_extension(filepath, gz_as_compressed)
        try:
            file = open(filepath, "rb")
            if compressed: self.set_header('Content-Encoding', 'gzip')
            self.set_header('Content-Type', get_mime(extension))
            gc.collect()
            while True:
                data = file.read(512)
                if len(data) == 0:
                    file.close()
                    return
                    
                self.write(data)
        except OSError as e:
            if e.errno == 2:
                self.status("404 Not Found")
            else:
                self.status("500 Internal Server Error")
        except Exception as e2:
            print(e2)
            self.status("500 Internal Server Error")
        finally:
            self.end()
        
    def write(self, content):
        self.set_header("Transfer-Encoding", "chunked")
        self.__http_write("%x" % len(content))
        self.__http_write(content)
        
    def end(self, content=""):
        if ("Transfer-Encoding", "chunked") in self.headers.items():
            if content != "":
                self.write(content)
            self.write("")
        else:
            self.__http_write(content)
            self.__http_write("")
        self.has_responded = True       
    
    async def close(self):
        await self.writer.drain()
        self.writer.close()
        await self.writer.wait_closed()
        
    def __http_start_response(self):
        if self.__start_response: return
        self.__write(' '.join([self.__version, self.__status]) + "\r\n")
        self.__start_response = True
        
    def __http_write(self, data):
        self.__http_start_response()
        self.__http_send_headers()
        self.__write(data)
        self.__write("\r\n")
        
    def __write(self, data):
        if self.has_responded:
            raise AlreadyRespondedError("Already responded to this request")
        if(type(data) is str):
            self.writer.write(bytes(data, 'utf-8'))
        else:
            self.writer.write(data)

        
    
    
class Request:
    def __init__(self, request, address):
        self.request = request.decode()
        self.address = address
        self.__parse_request()
    
    def __parse_request(self):
        self.raw_request = self.request.splitlines()
        if len(self.raw_request) < 2: raise InvalidRequestError("invalid http request")

        self.request_line = self.raw_request[0].split(' ')
        if len(self.request_line) < 3: raise InvalidRequestError("invalid http request")
        self.method = self.request_line[0].upper()
        self.route = self.request_line[1].lower()
        self.url_parts, query = self.__get_route_parser(self.route)
        if query != None:
            self.query = parse_query(query)
        self.version = self.request_line[2]
        self.headers = {}
        header_end = -1
        for idx, line in enumerate(self.raw_request):
            if line == "":
                header_end = idx
                break
        if header_end == -1:
            raise InvalidRequestError("invalid http request")
        self.headers = self.__parse_headers(self.raw_request[1:header_end])
        self.raw_body = '\n'.join(self.raw_request[header_end+1:])

    def __get_route_parser(self, route):
        url_query = route.split("?", 1)
        parts = list(filter(None, url_query[0].split("/")))
        if len(url_query) > 2:
            return parts, url_query[1]
        return parts, None

    def __parse_headers(self, header_block):
        headers = {}
        for header in header_block:
            key, value = self.__parse_header(header)
            if key == None: continue
            headers[key] = value
        return headers

    def __parse_header(self, raw_header):
        header = raw_header.split(':', 1)
        if len(header) < 2: return None, None
        return header[0].strip().lower(), header[1].strip().lower()

    


    def __str__(self):
        return self.request

   

#helper functions

#good enough to identify awaitable function

def files_exist(filepath):
    file = None
    comp_file = None
    try:
        os.stat(filepath)
        file = filepath
    except:
        pass
    try:
        os.stat(filepath + ".gz")
        comp_file = filepath + ".gz"
    except:
        pass
    return (file, comp_file)

def get_file_to_send(filepath, comp_file_policy):
    file, comp_file = files_exist(filepath)
    if comp_file_policy == Comp_File_Policy.NO_COMP: return (file, False)
    if comp_file_policy == Comp_File_Policy.ALL_COMP: return (file, True) if file is not None else (comp_file, True)
    if comp_file_policy == Comp_File_Policy.GZ_COMP: return (comp_file, True) if comp_file is not None else (file, False)

def iscoroutine(obj):
    return hasattr(obj, "send")

def parse_query(query):
    params = query.split("&")
    for param in params:
        pair = param.split("=", 1)
        if len(pair) == 1:
            pair.append("")
        return (parse_query_string(pair[0]), parse_query_string(pair[1]))

def parse_query_string(string):
    parsed_string = string
    for key, value in URL_ESCAPE.items():
        parsed_string = parsed_string.replace(key, value)
        parsed_string = parsed_string.replace(key.lower(), value)
    return parsed_string

URL_ESCAPE = {
    "%20": " ", "%3C": "<", "%3E": ">", "%23": "#", "%225": "%", "%2B": "+",
    "%7B": "{", "%7D": "}", "%7C": "|", "%5C": "\\", "%5E": "^", "%7E": "~",
    "%5B": "[", "%5D": "]", "%60": "‘", "%3B": ";", "%2F": "/", "%3F": "?",
    "%3A": ":", "%40": "@", "%3D": "=", "%26": "&", "%24": "$",
}

# if compressed=True return ext from file.ext.gz
# if file.ext.gz return compressed as second tuple value
def get_extension(file_name, gz_as_compressed=False):
    extension_match = file_name.split(".")
    length = len(extension_match)
    if length < 2: return (None, False)

    if gz_as_compressed and length > 2 and extension_match[-1].lower() == "gz":
        return (extension_match[-2], True)
    return (extension_match[-1], False)

def get_mime(extension):
    if extension is None: return "application/octet-stream"
    if extension.lower() in MIME_TYPES:
        return MIME_TYPES[extension]
    else:
        return "application/octet-stream"

def sanitize_path(path, strict=False):
    sanitized_path = path.replace("..", ".")
    if strict and sanitized_path != path: return ""
    return sanitized_path

def join_path(*paths):
    return ("/").join(paths)
