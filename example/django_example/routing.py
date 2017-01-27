from .consumer import MyJsonRpcWebsocketConsumer


channel_routing = [
    MyJsonRpcWebsocketConsumer.as_route(path=r"")

]
