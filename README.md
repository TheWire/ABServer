# ABServer
 
Micropython web application framework with Express.js like functionality.

## Example Usage

```
import ABServer
import uasyncio
import network

#route middleware
def home(request, response):
    response.send("hello world")

def main():

    wifi = network.WLAN(network.STA_IF)
    wifi.connect(secrets.SSID, secrets.PASSWORD)

    server = ABServer.Server(wifi)

    server.get("/", home)

    uasyncio.create_task(server.listen())

    while True:
        await uasyncio.sleep(1)
usyncio.run(main())
```

### Middleware Example
```
def middleware(response, request):
    response.set_header("Content-Type", "text/plain")
    response.write("some data") # send without ending response
    response.send("some more data") # send and end response
```

### Set Middleware
```
server.use('/path', middleware)
```

### Set Method Middlewares

```
server.get("/", middleware)
server.post("/", middleware)
server.put("/", middleware)
server.delete("/", middleware)
server.patch("/", middleware)
server.head("/", middleware)
```

### Serve Static Files

```
server.use('/static_route_, server.static('/static_file_path'))
```