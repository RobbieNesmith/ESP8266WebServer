import uasyncio

class ESP8266WebServer:
  def __init__(self, binding=("0.0.0.0", 80), backlog=5):
    self.binding = binding
    self.backlog = backlog
    self.routes = {}
    self._background_process = None
    self._not_found = self._default_not_found

  def run(self):
    uasyncio.create_task(uasyncio.start_server(self.server_callback, self.binding[0], self.binding[1]))
    if (self._background_process):
      uasyncio.create_task(self._background_process())
    uasyncio.get_event_loop().run_forever()
    
  async def _send_resp(self, writer, status=200, status_message="OK", payload="200 OK", headers={}):
    await writer.awrite('HTTP/1.0 {} {}\r\n'.format(status, status_message))
    for header in headers:
      await writer.awrite("{}: {}".format(header, headers[header]) + '\r\n')
    await writer.awrite('\r\n')
    await writer.awrite(payload)

  def server_callback(self, reader, writer):
    try:
      req = (await reader.read(1024)).decode("utf-8")
      if len(req):
        await self._process_route(writer, self._process_request(req))
      await writer.aclose()
    except OSError as e:
      pass

  def _process_query_param(self, query_param):
    key_value = query_param.split("=", 1)
    if len(key_value) == 2:
      return key_value
    elif len(key_value) == 1:
      return (key_value[0], "")

  def _process_request(self, req):
    method, req = req.split("\r\n", 1)
    method, path, protocol = method.split(" ")
    query_params = {}
    if "?" in path:
      path, query_params = path.split("?", 1)
      query_params = {qp[0]: qp[1] for qp in [self._process_query_param(query_param) for query_param in filter(len, query_params.split("&"))]}
    headers, req = req.split("\r\n\r\n", 1)
    headers = {kv[0]: kv[1] for kv in [header.split(": ", 1) for header in headers.split("\r\n")]}
    out = {}
    out["method"] = method
    out["path"] = path
    out["query_params"] = query_params
    out["protocol"] = protocol
    out["headers"] = headers
    out["req"] = req
    return out

  async def _process_route(self, writer, req_obj):
    if req_obj["path"] in self.routes:
      if req_obj["method"] in self.routes[req_obj["path"]]:
        await self._send_resp(writer, **self.routes[req_obj["path"]][req_obj["method"]](request_object=req_obj))
        return
    await self._send_resp(writer, **self._not_found(request_object=req_obj))

  def _default_not_found(self, request_object):
    return {"status": 404, "status_message": "Not Found", "payload": "404 Not Found"}

# Decorators

  def route(self, route, method="GET"):
    def route_deco(func):
      if route not in self.routes:
        self.routes[route] = {}
      self.routes[route][method] = func
      return func
    return route_deco
    
  def not_found(self, func):
    self._not_found = func
    return func

  def background_process(self, func):
    self._background_process = func
    return func