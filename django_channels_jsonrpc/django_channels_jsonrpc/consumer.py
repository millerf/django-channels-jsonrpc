from channels.generic.websockets import WebsocketConsumer, JsonWebsocketConsumer
from .jsonrpcwebsocketconsumer import JsonRpcWebsocketConsumer

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

    def receive(self, text=None, bytes=None, **kwargs):
        """
        Called when a message is received with decoded JSON content
        """
        # Simple echo
        print "received: %s" % text
        self.send(text)

    def disconnect(self, message, **kwargs):
        """
        Perform things on connection close
        """
        print "disconnect"





class MyJsonWebsocketConsumer(JsonRpcWebsocketConsumer):

    # Set to True if you want them, else leave out
    strict_ordering = False
    slight_ordering = False

    def connection_groups(self, **kwargs):
        """
        Called to return the list of groups to automatically add/remove
        this connection to/from.
        """
        return ["test"]

    def receive(self, content, **kwargs):
        """
        Called when a message is received with decoded JSON content
        """
        # Simple echo
        print "received: %s" % content
        print "kwargs %s" % kwargs
        self.send(content)

    def disconnect(self, message, **kwargs):
        """
        Perform things on connection close
        """
        print "disconnect"


@MyJsonWebsocketConsumer.rpc_method()
def ping():
    return "pong"