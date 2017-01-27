from .consumer import MyJsonRpcWebsocketConsumer
from channels.generic.websockets import WebsocketConsumer, JsonWebsocketConsumer


channel_routing = [
    MyJsonRpcWebsocketConsumer.as_route(path=r"")

]
