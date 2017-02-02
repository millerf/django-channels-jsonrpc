from channels_jsonrpc import JsonRpcWebsocketConsumerTest
# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

class MyJsonRpcWebsocketConsumerTest(JsonRpcWebsocketConsumerTest):

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
        logger.info("connect")

        # Do stuff if needed

    def disconnect(self, message, **kwargs):
        """
        Perform things on connection close
        """
        logger.info("disconnect")

        # Do stuff if needed

@MyJsonRpcWebsocketConsumerTest.rpc_method()
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