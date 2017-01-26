from channels.generic.websockets import WebsocketConsumer
from .jsonrpc import JsonRpcBase
import json




class JsonRpcException(Exception):
    """
    >>> exc = JsonRpcException(1, INVALID_REQUEST)
    >>> str(exc)
    '{"jsonrpc": "2.0", "id": 1, "error": {"message": "Invalid Request", "code": -32600}}'

    """

    def __init__(self, rpc_id, code, data=None):
        self.rpc_id = rpc_id
        self.code = code
        self.data = data

    @property
    def message(self):
        return errors[self.code]

    def as_dict(self):
        if self.data:
            return {'jsonrpc': '2.0',
                    'id': self.rpc_id,
                    'error': {'code': self.code,
                              'message': self.message,
                              'data': self.data}}
        else:
            return {'jsonrpc': '2.0',
                    'id': self.rpc_id,
                    'error': {'code': self.code,
                              'message': self.message}}

    def __str__(self):
        return json.dumps(self.as_dict())



"""
http://groups.google.com/group/json-rpc/web/json-rpc-2-0

errors:

code 	message 	meaning
-32700 	Parse error 	Invalid JSON was received by the server.
An error occurred on the server while parsing the JSON text.
-32600 	Invalid Request 	The JSON sent is not a valid Request object.
-32601 	Method not found 	The method does not exist / is not available.
-32602 	Invalid params 	Invalid method parameter(s).
-32603 	Internal error 	Internal JSON-RPC error.
-32099 to -32000 	Server error 	Reserved for implementation-defined server-errors.

"""
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603
GENERIC_APPLICATION_ERROR = -32000

errors = {}
errors[PARSE_ERROR] = "Parse Error"
errors[INVALID_REQUEST] = "Invalid Request"
errors[METHOD_NOT_FOUND] = "Method Not Found"
errors[INVALID_PARAMS] = "Invalid Params"
errors[INTERNAL_ERROR] = "Internal Error"
errors[GENERIC_APPLICATION_ERROR] = "Application Error"


class JsonRpcWebsocketConsumer(WebsocketConsumer):
    """
    Variant of WebsocketConsumer that automatically JSON-encodes and decodes
    messages as they come in and go out. Expects everything to be text; will
    error on binary data.
    """

    avail_methods = {}

    @staticmethod
    def rpc_method(rpc_name=None):
        """
        Decorator to list RPC methodds available. An optionnal name can be added
        :param rpc_name:
        :return:
        """
        def wrap(f):
            name = rpc_name if rpc_name is not None else f.func_name
            JsonRpcWebsocketConsumer.avail_methods[name] = f
            print JsonRpcWebsocketConsumer.avail_methods
        return wrap


    def error(self, id, code, message):
        return {
                    'jsonrpc': '2.0',
                    'id': id,
                    'error': {
                        'code': code,
                        'message': message
                        }
                    }
    def raw_receive(self, message, **kwargs):

        if "text" in message:
            try:
                data = json.loads(message['text'])
                if isinstance(data, dict):
                    # resdata = self._call(data, extra_vars)
                    # ACTUAL CALL
                    print "heeeeereee"
                    pass
                elif isinstance(data, list):
                    if len([x for x in data if not isinstance(x, dict)]):
                        resdata = self.error(None, INVALID_REQUEST, errors[INVALID_REQUEST])
            except Exception, e:
                resdata = self.error(None, INVALID_REQUEST, errors[INVALID_REQUEST])

        else:
            resdata = self.error(None, INVALID_REQUEST, errors[INVALID_REQUEST])

        self.send(resdata)


    def receive(self, content, **kwargs):
        """
        Called with decoded JSON content.
        """
        pass

    def send(self, content, close=False):
        """
        Encode the given content as JSON and send it to the client.
        """
        super(JsonRpcWebsocketConsumer, self).send(text=json.dumps(content), close=close)

    @classmethod
    def group_send(cls, name, content, close=False):
        WebsocketConsumer.group_send(name, json.dumps(content), close=close)