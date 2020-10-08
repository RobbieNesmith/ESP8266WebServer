import uasyncio
import usocket as socket
import uselect as select

class ESP8266WebServer:
  def __init__(self, binding=("0.0.0.0", 80), backlog=5):
    self.binding = binding
    self.backlog = backlog
    self.routes = {}
    self._background_process = None
    self._not_found = self._default_not_found
    self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.server.bind(self.binding)

  def run(self):
    self.server.listen(self.backlog)
    uasyncio.create_task(self._server_loop())
    if (self._background_process):
      uasyncio.create_task(self._background_process())
    uasyncio.get_event_loop().run_forever()
    
  def _send_resp(self, client, status=200, status_message="OK", payload="200 OK", headers={}):
    client.send('HTTP/1.0 {} {}\r\n'.format(status, status_message))
    for header in headers:
      client.send("{}: {}".format(header, headers[header]) + '\r\n')
    client.send('\r\n')
    client.send(payload)

  async def _server_loop(self):
    while(True):
      r, w, err = select.select((self.server,), (), (), 1)
      if r:
        for readable in r:
          client, client_addr = self.server.accept()
          try:
            req = client.recv(1024).decode("utf-8")
            if len(req):
              self._process_route(client, self._process_request(req))
            client.close()
          except OSError as e:
            pass
      await uasyncio.sleep(0.1)

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

  def _process_route(self, client, req_obj):
    if req_obj["path"] in self.routes:
      if req_obj["method"] in self.routes[req_obj["path"]]:
        self._send_resp(client, **self.routes[req_obj["path"]][req_obj["method"]](request_object=req_obj))
        return
    self._send_resp(client, **self._not_found(request_object=req_obj))

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