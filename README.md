# ESP8266WebServer

This is a (very) simple web server that you can use on an ESP8266 running MicroPython.

It should be enough to set up a basic web server or API without taking up too much space.

## Example Usage

```
import uasyncio

from ESP8266WebServer import ESP8266WebServer

e = ESP8266WebServer()

# Decorator routes!

@e.route("/")
def index(request_object):
    return {"payload": "Main Page"}

# Query parameters!

@e.route("/other/page")
def other_page(request_object):
    if "secret" not in request_object["query_params"]:
        return {"status": 400, "status_message": "Bad Request", "payload": '{"reason": "no reason"}', "headers": {"Content-type": "application/json"}}
    return {"payload": "Nice! You found the secret"}

# 404 pages!

@e.not_found
def not_found(request_object):
    return {"payload": "{} not found on this server".format(request_object["path"])}

# Background tasks!

@e.background_process
async def background():
    while True:
        print("checking the temp/humidity sensor on pins 4 and 5...")
        await uasyncio.sleep(10);

e.run()
```