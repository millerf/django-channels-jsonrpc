# Django-channels-jsonrpc

[![PyPI version](https://badge.fury.io/py/django-channels-jsonrpc.svg)](https://badge.fury.io/py/django-channels-jsonrpc) [![Codacy Badge](https://api.codacy.com/project/badge/Grade/04d12270939d47689756edda41e9f69f)](https://www.codacy.com/app/MosaicVenture/django-channels-jsonrpc?utm_source=github.com&utm_medium=referral&utm_content=millerf/django-channels-jsonrpc&utm_campaign=badger) [![Build Status](https://travis-ci.org/millerf/django-channels-jsonrpc.svg?branch=master)](https://travis-ci.org/millerf/django-channels-jsonrpc) [![Coverage Status](https://coveralls.io/repos/github/millerf/django-channels-jsonrpc/badge.svg)](https://coveralls.io/github/millerf/django-channels-jsonrpc) [![Code Climate](https://codeclimate.com/github/millerf/django-channels-jsonrpc/badges/gpa.svg)](https://codeclimate.com/github/millerf/django-channels-jsonrpc)

The Django-channels-jsonrpc is aimed to enable [JSON-RPC](http://json-rpc.org/) functionnality on top of the excellent django channels project and especially their Websockets functionality.
It is aimed to be:
  - Fully integrated with Channels
  - Fully implement JSON-RPC 1 and 2 protocol
  - Support both WebSocket and HTTP transports
  - Easy integration

## Tech


The only Django-channels-jsonrpc dependency is the [Django channels project](https://github.com/django/channels)

## Installation


Download and extract the [latest pre-built release](https://github.com/joemccann/dillinger/releases).

Install the dependencies and devDependencies and start the server.

```sh
$ pip install django-channels-jsonrpc
```


## Use


See complete example [here](https://github.com/millerf/django-channels-jsonrpc/blob/master/example/django_example/), and in particular [consumer.py](https://github.com/millerf/django-channels-jsonrpc/blob/master/example/django_example/)

It is intended to be used as a Websocket consumer. See [documentation](http://channels.readthedocs.io/en/stable/generics.html#websockets) except... simplier...

Import JsonRpcConsumer class and create the consumer

```python
from channels_jsonrpc import JsonRpcConsumer

class MyJsonRpcConsumer(JsonRpcConsumer):

    def connect(self, message, **kwargs):
        """
        Perform things on WebSocket connection start
        """
        self.message.reply_channel.send({"accept": True})

        print("connect")
        # Do stuff if needed

    def disconnect(self, message, **kwargs):
        """
        Perform things on WebSocket connection close
        """
        print("disconnect")
        # Do stuff if needed

```
JsonRpcConsumer derives from Channels WebSocketConsumer, you can read about all it's features here:
https://channels.readthedocs.io/en/stable/generics.html#websockets

Then the last step is to create the RPC methos hooks. IT is done with the decorator:
```python
@MyJsonRpcConsumer.rpc_method()
````


Like this:

```python
@MyJsonRpcConsumer.rpc_method()
def ping():
    return "pong"
```


**MyJsonRpcConsumer.rpc_method()** accept a *string* as a parameter to 'rename' the function
```python
@MyJsonRpcConsumer.rpc_method("mymodule.rpc.ping")
def ping():
    return "pong"
```

Will now be callable with "method":"mymodule.rpc.ping" in the rpc call:
```javascript
{"id":1, "jsonrpc":"2.0","method":"mymodule.rpc.ping","params":{}}
```

RPC methods can obviously accept parameters. They also return "results" or "errors":
```python
@MyJsonRpcConsumer.rpc_method("mymodule.rpc.ping")
def ping(fake_an_error):
    if fake_an_error:
        # Will return an error to the client
        #  --> {"id":1, "jsonrpc":"2.0","method":"mymodule.rpc.ping","params":{}}
        #  <-- {"id": 1, "jsonrpc": "2.0", "error": {"message": "fake_error", "code": -32000, "data": ["fake_error"]}}
        raise Exception("fake_error")
    else:
        # Will return a result to the client
        #  --> {"id":1, "jsonrpc":"2.0","method":"mymodule.rpc.ping","params":{}}
        #  <-- {"id": 1, "jsonrpc": "2.0", "result": "pong"}
        return "pong"
```

## [Sessions and other parameters from Message object](#message-object)
The original channel message - that can contain sessions (if activated with [http_user](https://channels.readthedocs.io/en/stable/generics.html#websockets)) and other important info  can be easily accessed by retrieving the `**kwargs` and get a parameter named *original_message*

```python
MyJsonRpcConsumerTest.rpc_method()
def json_rpc_method(param1, **kwargs):
    original_message = kwargs["orginal_message"]
    ##do something with original_message
```

Example:

```python
class MyJsonRpcConsumerTest(JsonRpcConsumer):
    # Set to True to automatically port users from HTTP cookies
    # (you don't need channel_session_user, this implies it)
    # https://channels.readthedocs.io/en/stable/generics.html#websockets
    http_user = True

....

@MyJsonRpcConsumerTest.rpc_method()
    def ping(**kwargs):
        original_message = kwargs["orginal_message"]
        original_message.channel_session["test"] = True
        return "pong"


```

## Notifications
### Inbound notifications
Those are the one sent from the client to the server.
They are dealt with the same way RPC methods are, except that instead of using `rpc_method()`, you can use `rpc_notification()`
Thos `rpc_notifications` can also retrieve the [`original_message`](#message-object) object
```
# Will be triggered when receiving this
#  --> {"jsonrpc":"2.0","method":"notification.alt_name","params":["val_param1", "val_param2"]}
@MyJsonRpcWebsocketConsumerTest.rpc_notification("notification.alt_name")
def notification1(param1, param2, **kwargs):
    original_message = kwargs["orginal_message"]
    # Do something with notification
    # ...
    # Notification shouldn't return anything.
    return
```

### Outbound notifications
The server might want to send notifications to one or more of its clients. For that `JsonRpcWebsocketConsumer` provides 2 static methods:
 - **JsonRpcWebsocketConsumer.notify_group(*group_name*, *method*, *params*)**

Using [channels'groups](https://channels.readthedocs.io/en/stable/concepts.html#groups) you can notify a whole group using this method
```
@MyJsonRpcWebsocketConsumerTest.rpc_method()
def send_to_group(group_name):
    MyJsonRpcWebsocketConsumerTest.notify_group(group_name, "notification.notif", {"payload": 1234})
    return True
```
Calling the RPC-method will send this notification to all the group *group_name*


 - **JsonRpcWebsocketConsumer.notify_channel(*reply_channel*, *method*, *params*)**

This will notify only *one* channel/client.

```
@MyJsonRpcWebsocketConsumerTest.rpc_method()
def send_to_reply_channel(**kwargs):
    original_message = kwarg["original_message"]
    MyJsonRpcWebsocketConsumerTest.notify_channel(original_message.reply_channel,
                                                "notification.ownnotif",
                                                {"payload": 12})
    return True

```

The `reply_channel` can be found in the[`original_message`](#message-object) object.

### Transport-specific rpc-method/notifications
If you want to restrict rpc methods or notifications access to a specific transport method (http or websocket)
The two decorator `rpc_method()` and `rpc_notification()` accept parameters to restric their use. `websocket` (default: True) and `http` (default: True)

You can use them like this:
```
@MyJsonRpcWebsocketConsumerTest.rpc_notification("notification.alt_name", websocket=True, http=False)
def notification1(param1, param2, **kwargs):
    original_message = kwargs["orginal_message"]
    # This notification will only be used when using websocket transport
    return
```



## Custom JSON encoder class

```python
from django.core.serializers.json import DjangoJSONEncoder


class DjangoJsonRpcConsumer(JsonRpcConsumer):
    json_encoder_class = DjangoJSONEncoder
```

## Testing


The JsonRpcConsumer class can be tested the same way Channels Consumers are tested.
See [here](http://channels.readthedocs.io/en/stable/testing.html)

You just need to remember to set your JsonRpcConsumer class to TEST_MODE in the test:

```python
from channels.tests import ChannelTestCase, HttpClient
from .consumer import MyJsonRpcConsumer

MyJsonRpcConsumer.TEST_MODE = True



class TestsJsonConsumer(ChannelTestCase):
    def assertResult(self, method, params, result, error=False):
        client = HttpClient()
        client.send_and_consume('websocket.receive', text=request(method, params))
        key = "result" if not error else "error"
        message = client.receive()
        if message is None or key not in message:
            raise KeyError("'%s' key not in message: %s" % (key, message))

        self.assertEquals(message[key], result)

    def assertError(self, method, params, result):
        self.assertResult(method, params, result, True)

    def test_assert_result(self):

         self.assertResult("ping", {}, "pong")
```

## License


MIT

*Have fun with Websockets*!

**Free Software, Hell Yeah!**

[//]: # (These are reference links used in the body of this note and get stripped out when the markdown processor does its job. There is no need to format nicely because it shouldn't be seen. Thanks SO - http://stackoverflow.com/questions/4823468/store-comments-in-markdown-syntax)

