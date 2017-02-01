from .consumer import MyJsonRpcWebsocketConsumerTest


channel_routing = [
    MyJsonRpcWebsocketConsumerTest.as_route(path=r"")
]
