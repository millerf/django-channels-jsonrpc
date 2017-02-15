from .consumer import MyJsonRpcWebsocketConsumerTest, DjangoJsonRpcWebsocketConsumerTest


channel_routing = [
    DjangoJsonRpcWebsocketConsumerTest.as_route(path=r"^/django/$"),
    MyJsonRpcWebsocketConsumerTest.as_route(path=r""),
]
