from channels.tests import ChannelTestCase, HttpClient
from .jsonrpcwebsocketconsumer import JsonRpcWebsocketConsumer
from .consumer import MyJsonRpcWebsocketConsumer


class TestsJsonRPCWebsocketConsumer(ChannelTestCase):

    def test_connection(self):
        # Test connection
        client = HttpClient()
        client.send_and_consume(u'websocket.connect')
        self.assertEquals(client.receive(), None)

    def test_response_are_well_formatted(self):
        # Answer should always json-rpc2
        client = HttpClient()
        client.send_and_consume(u'websocket.receive', {'value': 'my_value'})

        response = client.receive()
        self.assertEqual(response['error'], {u'code': JsonRpcWebsocketConsumer.INVALID_REQUEST,
                                             u'message': JsonRpcWebsocketConsumer.errors[JsonRpcWebsocketConsumer.INVALID_REQUEST]})
        self.assertEqual(response['jsonrpc'], '2.0')
        self.assertEqual(response['id'], None)

    def test_inadequate_request(self):

        client = HttpClient()

        client.send_and_consume(u'websocket.receive', {'value': 'my_value'})
        self.assertEqual(client.receive()['error'], {u'code': JsonRpcWebsocketConsumer.INVALID_REQUEST,
                                                     u'message': JsonRpcWebsocketConsumer.errors[JsonRpcWebsocketConsumer.INVALID_REQUEST]})

        client.send_and_consume(u'websocket.receive', text='{"value": "my_value"}')
        self.assertEqual(client.receive()['error'], {u'code': JsonRpcWebsocketConsumer.INVALID_REQUEST,
                                                     u'message': JsonRpcWebsocketConsumer.errors[JsonRpcWebsocketConsumer.INVALID_REQUEST]})

        client.send_and_consume(u'websocket.receive', text='sqwdw')
        self.assertEqual(client.receive()['error'], {u'code': JsonRpcWebsocketConsumer.PARSE_ERROR,
                                                     u'message': JsonRpcWebsocketConsumer.errors[JsonRpcWebsocketConsumer.PARSE_ERROR]})

        client.send_and_consume(u'websocket.receive', {})
        self.assertEqual(client.receive()['error'], {u'code': JsonRpcWebsocketConsumer.INVALID_REQUEST,
                                                     u'message': JsonRpcWebsocketConsumer.errors[JsonRpcWebsocketConsumer.INVALID_REQUEST]})

        client.send_and_consume(u'websocket.receive', text=None)
        self.assertEqual(client.receive()['error'], {u'code': JsonRpcWebsocketConsumer.INVALID_REQUEST,
                                                     u'message': JsonRpcWebsocketConsumer.errors[JsonRpcWebsocketConsumer.INVALID_REQUEST]})

    def test_parsing_with_bad_request(self):
        # Test that parsing a bad request works

        client = HttpClient()

        client.send_and_consume(u'websocket.receive', text='{"id":"2", "method":"ping2", "params":{}}')
        self.assertEqual(client.receive()['error'], {u'code': JsonRpcWebsocketConsumer.INVALID_REQUEST,
                                                     u'message': JsonRpcWebsocketConsumer.errors[JsonRpcWebsocketConsumer.INVALID_REQUEST]})

    def test_notification(self):
        # Test that parsing a bad request works

        client = HttpClient()

        client.send_and_consume(u'websocket.receive', text='{"jsonrpc":"2.0", "method":"a_notif", "params":{}}')
        self.assertEqual(client.receive(), None)

    def test_method(self):
        @MyJsonRpcWebsocketConsumer.rpc_method()
        def ping2():
            return "pong2"

        client = HttpClient()

        client.send_and_consume(u'websocket.receive', text='{"id":1, "jsonrpc":"2.0", "method":"ping2", "params":{}}')
        msg = client.receive()
        self.assertEqual(msg['result'], "pong2")

    def test_parsing_with_good_request_wrong_params(self):
        @JsonRpcWebsocketConsumer.rpc_method()
        def ping2():
            return "pong2"

        # Test that parsing a ping request works
        client = HttpClient()

        client.send_and_consume(u'websocket.receive',
                                text='{"id":1, "jsonrpc":"2.0", "method":"ping2", "params":["test"]}')
        msg = client.receive()
        self.assertIn(msg['error']['message'],
                      [u'ping2() takes 0 positional arguments but 1 was given',
                       u'ping2() takes no arguments (1 given)'])

    def test_parsing_with_good_request(self):
        # Test that parsing a ping request works
        client = HttpClient()

        client.send_and_consume(u'websocket.receive', text='{"id":1, "jsonrpc":"2.0", "method":"ping", "params":{}}')
        msg = client.receive()
        self.assertEqual(msg['result'], "pong")

    def test_id_on_good_request(self):
        # Test that parsing a ping request works
        client = HttpClient()

        client.send_and_consume(u'websocket.receive', text='{"id":52, "jsonrpc":"2.0", "method":"ping", "params":{}}')
        msg = client.receive()
        self.assertEqual(msg['id'], 52)

    def test_id_on_errored_request(self):
        # Test that parsing a ping request works
        client = HttpClient()

        client.send_and_consume(u'websocket.receive',
                                text='{"id":52, "jsonrpc":"2.0", "method":"ping", "params":["test"]}')
        msg = client.receive()
        self.assertEqual(msg['id'], 52)


    def test_get_rpc_methods(self):

        class TestMyJsonRpcConsumer(JsonRpcWebsocketConsumer):
            pass

        @TestMyJsonRpcConsumer.rpc_method()
        def ping3():
            return "pong3"

        class TestMyJsonRpcConsumer2(JsonRpcWebsocketConsumer):
            pass
        @TestMyJsonRpcConsumer2.rpc_method()
        def ping4():
            return "pong4"

        methods = TestMyJsonRpcConsumer.get_rpc_methods()
        self.assertEquals(methods, ['ping3'])
        self.assertEquals(TestMyJsonRpcConsumer2.get_rpc_methods(), ['ping4'])

    def test_get_rpc_methods_with_name(self):

        class TestMyJsonRpcConsumer(JsonRpcWebsocketConsumer):
            pass

        @TestMyJsonRpcConsumer.rpc_method('test.ping.rpc')
        def ping5():
            return "pong5"

        self.assertEquals(TestMyJsonRpcConsumer.get_rpc_methods(), ['test.ping.rpc'])

    def test_error_on_rpc_call(self):
        @MyJsonRpcWebsocketConsumer.rpc_method()
        def ping_with_error():
            raise Exception("pong_with_error")

        # Test that parsing a ping request works
        client = HttpClient()

        client.send_and_consume(u'websocket.receive',
                                text='{"id":1, "jsonrpc":"2.0", "method":"ping_with_error", "params":{}}')
        msg = client.receive()
        self.assertEqual(msg['error']['message'], u'pong_with_error')
