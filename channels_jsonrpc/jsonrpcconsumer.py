import json
import logging

from channels.generic.websockets import WebsocketConsumer
from django.http import HttpResponse
from channels.handler import AsgiHandler, AsgiRequest
from six import string_types

# Get an instance of a logger
logger = logging.getLogger(__name__)


class JsonRpcException(Exception):
    """
    >>> exc = JsonRpcException(1, JsonRpcConsumer.INVALID_REQUEST)
    >>> str(exc)
    '{"jsonrpc": "2.0", "id": 1, "error": {"message": "Invalid Request", "code": -32600}}'

    """

    def __init__(self, rpc_id, code, data=None):
        self.rpc_id = rpc_id
        self.code = code
        self.data = data

    @property
    def message(self):
        return JsonRpcConsumer.errors[self.code]

    def as_dict(self):
        return JsonRpcConsumer.error(self.rpc_id, self.code, self.message, self.data)

    def __str__(self):
        return json.dumps(self.as_dict())


class MethodNotSupported(Exception):
    pass


class JsonRpcConsumer(WebsocketConsumer):
    """
    Variant of WebsocketConsumer that automatically JSON-encodes and decodes
    messages as they come in and go out. Expects everything to be text; will
    error on binary data.

    http://groups.google.com/group/json-rpc/web/json-rpc-2-0
    errors:
    code 	message 	meaning
    -32700 	Parse error 	Invalid JSON was received by the server.
            An error occurred on the server while parsing the JSON text.
    -32600 	Invalid Request 	The JSON sent is not a valid Request object.
    -32601 	Method not found 	The method does not exist / is not available.
    -32602 	Invalid params 	Invalid method parameter(s).
    -32603 	Internal error 	Internal JSON-RPC error.
    -32099 to -32000
            Server error 	Reserved for implementation-defined server-errors. (@TODO)

    """
    # Add http.request alogn with default websocket events
    method_mapping = {
        "websocket.connect": "raw_connect",
        "websocket.receive": "raw_receive",
        "websocket.disconnect": "raw_disconnect",
        "http.request": "http_handler"
    }

    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    GENERIC_APPLICATION_ERROR = -32000

    errors = dict()
    errors[PARSE_ERROR] = "Parse Error"
    errors[INVALID_REQUEST] = "Invalid Request"
    errors[METHOD_NOT_FOUND] = "Method Not Found"
    errors[INVALID_PARAMS] = "Invalid Params"
    errors[INTERNAL_ERROR] = "Internal Error"
    errors[GENERIC_APPLICATION_ERROR] = "Application Error"

    _http_codes = {
        PARSE_ERROR: 500,
        INVALID_REQUEST: 400,
        METHOD_NOT_FOUND: 404,
        INVALID_PARAMS: 500,
        INTERNAL_ERROR: 500,
        GENERIC_APPLICATION_ERROR: 500
    }

    json_encoder_class = None

    available_rpc_methods = dict()

    @classmethod
    def rpc_method(cls, rpc_name=None, websocket=True, http=True):
        """
        Decorator to list RPC methodds available. An optional name and protocol rectrictions can be added
        :param str rpc_name:
        :param bool websocket:
        :param bool http:
        :return: decorated function
        """
        def wrap(f):
            name = rpc_name if rpc_name is not None else f.__name__
            cid = id(cls)
            if cid not in cls.available_rpc_methods:
                cls.available_rpc_methods[cid] = dict()
            f.options = dict(websocket=websocket, http=http)
            cls.available_rpc_methods[cid][name] = f

            return f

        return wrap

    @classmethod
    def get_rpc_methods(cls):
        """
        Returns the RPC methods available for this consumer
        :return: list
        """
        if id(cls) not in cls.available_rpc_methods:
            return []
        return list(cls.available_rpc_methods[id(cls)].keys())

    @staticmethod
    def error(_id, code, message, data=None):
        """
        Error-type answer generator
        :param _id: int
        :param code: code of the error
        :param message: message for the error
        :param data: (optional) error data
        :return: object
        """
        error = {'jsonrpc': '2.0', "error": {'code': code, 'message': message}}
        if data is not None:
            error["error"]["data"] = data
        if _id:
            error["id"] = _id

        return error

    def http_handler(self, message):
        """
        Called on HTTP request
        :param message: message received
        :return: 
        """
        # Get Django HttpRequest object from ASGI Message
        request = AsgiRequest(message)

        # Try to process content
        try:
            if request.method != 'POST':
                raise MethodNotSupported('Only POST method is supported')
            content = request.body.decode('utf-8')
        except (UnicodeDecodeError, MethodNotSupported):
            content = ''
        result = self.__handle(content, message)

        # Set response status code
        status_code = 200
        if 'error' in result:
            status_code = self._http_codes[result['error']['code']]

        # Encode that response into message format (ASGI)
        response = HttpResponse(self._encode(result), content_type='application/json-rpc', status=status_code)
        for chunk in AsgiHandler.encode_response(response):
            message.reply_channel.send(chunk)

    def raw_receive(self, message, **kwargs):
        """
        Called when receiving a message.
        :param message: message received
        :param kwargs:
        :return:
        """
        content = '' if "text" not in message else message["text"]
        result = self.__handle(content, message)

        # Send responce back
        self.send(text=self._encode(result))

    def __handle(self, content, message):
        """
        Handle 
        :param content: 
        :param message: 
        :return: 
        """
        result = ''
        if content != '':
            try:
                data = json.loads(content)
            except ValueError:
                # json could not decoded
                result = self.error(None, self.PARSE_ERROR, self.errors[self.PARSE_ERROR])
            else:
                if isinstance(data, dict):

                    if data.get('method') is not None and data.get('params') is not None and data.get('id') is None:
                        # TODO: implement notifications support
                        return

                    try:
                        result = self.__process(data, message)
                    except JsonRpcException as e:
                        result = e.as_dict()
                    except Exception as e:
                        logger.exception('Application error')
                        result = self.error(data.get('id'),
                                            self.GENERIC_APPLICATION_ERROR,
                                            str(e),
                                            e.args[0] if len(e.args) == 1 else e.args)
                elif isinstance(data, list):
                    # TODO: implement batch calls
                    if len([x for x in data if not isinstance(x, dict)]):
                        result = self.error(None, self.INVALID_REQUEST, self.errors[self.INVALID_REQUEST])

        else:
            result = self.error(None, self.INVALID_REQUEST, self.errors[self.INVALID_REQUEST])

        return result

    def _encode(self, data):
        """
        Encode data object to JSON string
        :param data: 
        :return: 
        """
        return json.dumps(data, cls=self.json_encoder_class)

    @classmethod
    def __process(cls, data, original_msg):
        """
        Process the recived data
        :param dict data: 
        :param channels.message.Message original_msg:
        :return: dict
        """

        if data.get('jsonrpc') != "2.0":
            raise JsonRpcException(data.get('id'), cls.INVALID_REQUEST)

        if 'method' not in data:
            raise JsonRpcException(data.get('id'), cls.INVALID_REQUEST)

        methodname = data['method']
        if not isinstance(methodname, string_types):
            raise JsonRpcException(data.get('id'), cls.INVALID_REQUEST)

        if methodname.startswith('_'):
            raise JsonRpcException(data.get('id'), cls.METHOD_NOT_FOUND)

        try:
            method = cls.available_rpc_methods[id(cls)][methodname]
            proto = original_msg.channel.name.split('.')[0]
            if not method.options[proto]:
                raise MethodNotSupported('Method not available through %s' % proto)
        except (KeyError, MethodNotSupported):
            raise JsonRpcException(data.get('id'), cls.METHOD_NOT_FOUND)
        params = data.get('params', [])

        if not isinstance(params, (list, dict)):
            raise JsonRpcException(data.get('id'), cls.INVALID_PARAMS)

        if isinstance(params, list):
            result = method(*params, original_message=original_msg)
        else:
            result = method(original_message=original_msg, **params)

        return {
            'id': data.get('id'),
            'jsonrpc': '2.0',
            'result': result,
        }


class JsonRpcConsumerTest(JsonRpcConsumer):

    @classmethod
    def clean(cls):
        """
        Clean the class method name for tests
        :return: None
        """
        if id(cls) in cls.available_rpc_methods:
            del cls.available_rpc_methods[id(cls)]
