# Django-channels-jsonrpc

[![PyPI version](https://badge.fury.io/py/django-channels-jsonrpc.svg)](https://badge.fury.io/py/django-channels-jsonrpc) [![Codacy Badge](https://api.codacy.com/project/badge/Grade/04d12270939d47689756edda41e9f69f)](https://www.codacy.com/app/MosaicVenture/django-channels-jsonrpc?utm_source=github.com&utm_medium=referral&utm_content=millerf/django-channels-jsonrpc&utm_campaign=badger) [![Build Status](https://travis-ci.org/millerf/django-channels-jsonrpc.svg?branch=master)](https://travis-ci.org/millerf/django-channels-jsonrpc) [![Coverage Status](https://coveralls.io/repos/github/millerf/django-channels-jsonrpc/badge.svg)](https://coveralls.io/github/millerf/django-channels-jsonrpc)


The Django-channels-jsonrpc is aimed to enable [JSON-RPC](http://json-rpc.org/) functionnality on top of the excellent django channels project and especially their Websockets functionality.
It is aimed to be:
  - Fully integrated with Channels
  - Fully implement JSON-RPC 1 and 2 protocol
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


See complete exmaple [here](https://github.com/millerf/django-channels-jsonrpc/blob/master/example/django_example/), and in particular [consumer.py](https://github.com/millerf/django-channels-jsonrpc/blob/master/example/django_example/)

It is intended to be used as a Websocket consumer. See [documentation](http://channels.readthedocs.io/en/stable/generics.html#websockets) except... simplier...

Start importing the JsonRpcWebsocketConsumer class

```python
from channels_jsonrpc import JsonRpcWebsocketConsumer
```

And create the consumer

```python
class MyJsonRpcWebsocketConsumer(JsonRpcWebsocketConsumer):

    # Set to True if you want them, else leave out
    strict_ordering = False
    slight_ordering = False

    def connection_groups(self, **kwargs):
        """
        Called to return the list of groups to automatically add/remove
        this connection to/from.
        """
        return ["test"]

    def connect(self, message, **kwargs):
        """
        Perform things on connection start
        """
        self.message.reply_channel.send({"accept": True})
        print("connect")

        # Do stuff if needed

    def disconnect(self, message, **kwargs):
        """
        Perform things on connection close
        """
        print("disconnect")

        # Do stuff if needed

```

Then the last step is to create the RPC methos hooks. IT is done with the decorator:
```python
@MyJsonRpcWebsocketConsumer.rpc_method()
````


Like this:

```python
@MyJsonRpcWebsocketConsumer.rpc_method()
def ping():
    return "pong"
```


**MyJsonRpcWebsocketConsumer.rpc_method()** accept a *string* as a parameter to 'rename' the function
```python
@MyJsonRpcWebsocketConsumer.rpc_method("mymodule.rpc.ping")
def ping():
    return "pong"
```

Will now be callable with "method":"mymodule.rpc.ping" in the rpc call:
```javascript
{"id":1, "jsonrpc":"2.0","method":"mymodule.rpc.ping","params":{}}
```

RPC methods can obviously accept parameters. They also return "results" or "errors":
```python
@MyJsonRpcWebsocketConsumer.rpc_method("mymodule.rpc.ping")
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

## Sessions and other parameters from Message object
The original channel message - that can contains sessions (if activated with [http_user](https://channels.readthedocs.io/en/stable/generics.html#websockets)) and other important info  can be easily accessed by importing it from the package in a json_rpc method:

```python
MyJsonRpcWebsocketConsumerTest.rpc_method()
def json_rpc_method(param1):
    from channels_jsonrpc.jsonrpcwebsocketconsumer import original_message
    ##do something with original_message
```

Example:

```python
class MyJsonRpcWebsocketConsumerTest(JsonRpcWebsocketConsumer):
    # Set to True to automatically port users from HTTP cookies
    # (you don't need channel_session_user, this implies it)
    # https://channels.readthedocs.io/en/stable/generics.html#websockets
    http_user = True

....

@MyJsonRpcWebsocketConsumerTest.rpc_method()
    def ping():
        from channels_jsonrpc.jsonrpcwebsocketconsumer import original_message
        original_message.channel_session["test"] = True
        return "pong"


```


## Testing


The JsonRpcWebsocketConsumer class can be tested the same way Channels Consumers are tested.
See [here](http://channels.readthedocs.io/en/stable/testing.html)

You just need to remember to set your JsonRpcConsumer class to TEST_MODE in the test:

```python
from channels.tests import ChannelTestCase, HttpClient
from .consumer import MyJsonRpcWebsocketConsumer

MyJsonRpcWebsocketConsumer.TEST_MODE = True



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

         self.assertResult("ping", {},
                           "pong")
```

## License


MIT

*Have fun with Websockets*!

**Free Software, Hell Yeah!**

[//]: # (These are reference links used in the body of this note and get stripped out when the markdown processor does its job. There is no need to format nicely because it shouldn't be seen. Thanks SO - http://stackoverflow.com/questions/4823468/store-comments-in-markdown-syntax)


   [dill]: <https://github.com/joemccann/dillinger>
   [git-repo-url]: <https://github.com/joemccann/dillinger.git>
   [john gruber]: <http://daringfireball.net>
   [@thomasfuchs]: <http://twitter.com/thomasfuchs>
   [df1]: <http://daringfireball.net/projects/markdown/>
   [markdown-it]: <https://github.com/markdown-it/markdown-it>
   [Ace Editor]: <http://ace.ajax.org>
   [node.js]: <http://nodejs.org>
   [Twitter Bootstrap]: <http://twitter.github.com/bootstrap/>
   [keymaster.js]: <https://github.com/madrobby/keymaster>
   [jQuery]: <http://jquery.com>
   [@tjholowaychuk]: <http://twitter.com/tjholowaychuk>
   [express]: <http://expressjs.com>
   [AngularJS]: <http://angularjs.org>
   [Gulp]: <http://gulpjs.com>

   [PlDb]: <https://github.com/joemccann/dillinger/tree/master/plugins/dropbox/README.md>
   [PlGh]:  <https://github.com/joemccann/dillinger/tree/master/plugins/github/README.md>
   [PlGd]: <https://github.com/joemccann/dillinger/tree/master/plugins/googledrive/README.md>
   [PlOd]: <https://github.com/joemccann/dillinger/tree/master/plugins/onedrive/README.md>
