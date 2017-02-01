from channels_jsonrpc import JsonRpcWebsocketConsumerTest, JsonRpcException
from channels.tests import ChannelTestCase, HttpClient
from .consumer import MyJsonRpcWebsocketConsumerTest


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
        self.assertEqual(response['error'], {u'code': JsonRpcWebsocketConsumerTest.INVALID_REQUEST,
                                             u'message': JsonRpcWebsocketConsumerTest.errors[JsonRpcWebsocketConsumerTest.INVALID_REQUEST]})
        self.assertEqual(response['jsonrpc'], '2.0')
        self.assertEqual(response['id'], None)

    def test_inadequate_request(self):

        client = HttpClient()

        client.send_and_consume(u'websocket.receive', text='{"value": "my_value"}')
        self.assertEqual(client.receive()['error'], {u'code': JsonRpcWebsocketConsumerTest.INVALID_REQUEST,
                                                     u'message': JsonRpcWebsocketConsumerTest.errors[JsonRpcWebsocketConsumerTest.INVALID_REQUEST]})

        client.send_and_consume(u'websocket.receive')
        self.assertEqual(client.receive()['error'], {u'code': JsonRpcWebsocketConsumerTest.INVALID_REQUEST,
                                                     u'message': JsonRpcWebsocketConsumerTest.errors[
                                                         JsonRpcWebsocketConsumerTest.INVALID_REQUEST]})

        client.send_and_consume(u'websocket.receive', text='["value", "my_value"]')
        self.assertEqual(client.receive()['error'], {u'code': JsonRpcWebsocketConsumerTest.INVALID_REQUEST,
                                                     u'message': JsonRpcWebsocketConsumerTest.errors[
                                                         JsonRpcWebsocketConsumerTest.INVALID_REQUEST]})

        # missing "method"
        client.send_and_consume(u'websocket.receive', text='{"id":"2", "jsonrpc":"2.0", "params":{}}')
        self.assertEqual(client.receive()['error'], {u'code': JsonRpcWebsocketConsumerTest.INVALID_REQUEST,
                                                     u'message': JsonRpcWebsocketConsumerTest.errors[JsonRpcWebsocketConsumerTest.INVALID_REQUEST]})

        # wrong method name
        client.send_and_consume(u'websocket.receive', text='{"id":"2", "jsonrpc":"2.0", "method":2, "params":{}}')
        self.assertEqual(client.receive()['error'], {u'code': JsonRpcWebsocketConsumerTest.INVALID_REQUEST,
                                                     u'message': JsonRpcWebsocketConsumerTest.errors[
                                                         JsonRpcWebsocketConsumerTest.INVALID_REQUEST]})

        # wrong method name
        client.send_and_consume(u'websocket.receive', text='{"id":"2", "jsonrpc":"2.0", "method":"_test", "params":{}}')
        self.assertEqual(client.receive()['error'], {u'code': JsonRpcWebsocketConsumerTest.METHOD_NOT_FOUND,
                                                     u'message': JsonRpcWebsocketConsumerTest.errors[
                                                         JsonRpcWebsocketConsumerTest.METHOD_NOT_FOUND]})

        client.send_and_consume(u'websocket.receive', text='{"value": "my_value"}')
        self.assertEqual(client.receive()['error'], {u'code': JsonRpcWebsocketConsumerTest.INVALID_REQUEST,
                                                     u'message': JsonRpcWebsocketConsumerTest.errors[
                                                         JsonRpcWebsocketConsumerTest.INVALID_REQUEST]})

        client.send_and_consume(u'websocket.receive', text='sqwdw')
        self.assertEqual(client.receive()['error'], {u'code': JsonRpcWebsocketConsumerTest.PARSE_ERROR,
                                                     u'message': JsonRpcWebsocketConsumerTest.errors[JsonRpcWebsocketConsumerTest.PARSE_ERROR]})

        client.send_and_consume(u'websocket.receive', text='{}')
        self.assertEqual(client.receive()['error'], {u'code': JsonRpcWebsocketConsumerTest.INVALID_REQUEST,
                                                     u'message': JsonRpcWebsocketConsumerTest.errors[JsonRpcWebsocketConsumerTest.INVALID_REQUEST]})

        client.send_and_consume(u'websocket.receive', text=None)
        self.assertEqual(client.receive()['error'], {u'code': JsonRpcWebsocketConsumerTest.INVALID_REQUEST,
                                                     u'message': JsonRpcWebsocketConsumerTest.errors[JsonRpcWebsocketConsumerTest.INVALID_REQUEST]})

    def test_unexisting_method(self):
        # unknown method
        client = HttpClient()

        client.send_and_consume(u'websocket.receive',
                                text='{"id": 1, "jsonrpc": "2.0", "method": "unknown_method", "params": {}}')
        msg = client.receive()
        self.assertEqual(msg['error'], {u'code': JsonRpcWebsocketConsumerTest.METHOD_NOT_FOUND,
                                                     u'message': JsonRpcWebsocketConsumerTest.errors[
                                                         JsonRpcWebsocketConsumerTest.METHOD_NOT_FOUND]})

    def test_parsing_with_bad_request(self):
        # Test that parsing a bad request works

        client = HttpClient()

        client.send_and_consume(u'websocket.receive', text='{"id":"2", "method":"ping2", "params":{}}')
        self.assertEqual(client.receive()['error'], {u'code': JsonRpcWebsocketConsumerTest.INVALID_REQUEST,
                                                     u'message': JsonRpcWebsocketConsumerTest.errors[JsonRpcWebsocketConsumerTest.INVALID_REQUEST]})

    def test_notification(self):
        # Test that parsing a bad request works

        client = HttpClient()

        client.send_and_consume(u'websocket.receive', text='{"jsonrpc":"2.0", "method":"a_notif", "params":{}}')
        self.assertEqual(client.receive(), None)

    def test_method(self):
        @MyJsonRpcWebsocketConsumerTest.rpc_method()
        def ping2():
            return "pong2"

        client = HttpClient()

        client.send_and_consume(u'websocket.receive', text='{"id":1, "jsonrpc":"2.0", "method":"ping2", "params":{}}')
        msg = client.receive()
        self.assertEqual(msg['result'], "pong2")

    def test_parsing_with_good_request_wrong_params(self):
        @JsonRpcWebsocketConsumerTest.rpc_method()
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

    def test_parsing_with_good_request_ainvalid_paramas(self):
        @JsonRpcWebsocketConsumerTest.rpc_method()
        def ping2(test):
            return "pong2"

        # Test that parsing a ping request works
        client = HttpClient()

        client.send_and_consume(u'websocket.receive',
                                text='{"id":1, "jsonrpc":"2.0", "method":"ping2", "params":true}')
        msg = client.receive()
        self.assertEqual(msg['error'], {u'code': JsonRpcWebsocketConsumerTest.INVALID_PARAMS,
                                                     u'message': JsonRpcWebsocketConsumerTest.errors[
                                                         JsonRpcWebsocketConsumerTest.INVALID_PARAMS]})
    def test_parsing_with_good_request(self):
        # Test that parsing a ping request works
        client = HttpClient()

        client.send_and_consume(u'websocket.receive', text='{"id":1, "jsonrpc":"2.0", "method":"ping", "params":[false]}')
        msg = client.receive()
        self.assertEquals(msg['result'], "pong")

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

        class TestMyJsonRpcConsumer(JsonRpcWebsocketConsumerTest):
            pass

        @TestMyJsonRpcConsumer.rpc_method()
        def ping3():
            return "pong3"

        class TestMyJsonRpcConsumer2(JsonRpcWebsocketConsumerTest):
            pass
        @TestMyJsonRpcConsumer2.rpc_method()
        def ping4():
            return "pong4"

        methods = TestMyJsonRpcConsumer.get_rpc_methods()
        self.assertEquals(methods, ['ping3'])
        self.assertEquals(TestMyJsonRpcConsumer2.get_rpc_methods(), ['ping4'])

    def test_get_rpc_methods_with_name(self):

        class TestMyJsonRpcConsumer(JsonRpcWebsocketConsumerTest):
            pass

        @TestMyJsonRpcConsumer.rpc_method('test.ping.rpc')
        def ping5():
            return "pong5"

        self.assertEquals(TestMyJsonRpcConsumer.get_rpc_methods(), ['test.ping.rpc'])

    def test_error_on_rpc_call(self):
        @MyJsonRpcWebsocketConsumerTest.rpc_method()
        def ping_with_error():
            raise Exception("pong_with_error")

        # Test that parsing a ping request works
        client = HttpClient()

        client.send_and_consume(u'websocket.receive',
                                text='{"id":1, "jsonrpc":"2.0", "method":"ping_with_error", "params":{}}')
        msg = client.receive()
        self.assertEqual(msg['error']['message'], u'pong_with_error')

    def test_error_on_rpc_call_with_data(self):
        @MyJsonRpcWebsocketConsumerTest.rpc_method()
        def ping_with_error_data():
            raise JsonRpcException(1, JsonRpcWebsocketConsumerTest.GENERIC_APPLICATION_ERROR, data="test_data")

        # Test that parsing a ping request works
        client = HttpClient()

        client.send_and_consume(u'websocket.receive',
                                text='{"id":1, "jsonrpc":"2.0", "method":"ping_with_error_data", "params":{}}')
        msg = client.receive()
        self.assertEqual(msg['id'], 1)
        self.assertEqual(msg['error']['code'], JsonRpcWebsocketConsumerTest.GENERIC_APPLICATION_ERROR)
        self.assertEqual(msg['error']['data'], u'test_data')

    def test_namesake_consumers(self):

        # Changed name to TestNamesakeJsonRpcConsumer2 to prevent overlapping with "previous" TestMyJsonRpcConsumer

        class Context1():
            class TestNamesakeJsonRpcConsumer2(JsonRpcWebsocketConsumerTest):
                pass

        class Context2():
            class TestNamesakeJsonRpcConsumer2(JsonRpcWebsocketConsumerTest):
                pass

        @Context1.TestNamesakeJsonRpcConsumer.rpc_method()
        def method1():
          pass

        @Context2.TestNamesakeJsonRpcConsumer.rpc_method()
        def method2():
          pass

        self.assertEquals(Context1.TestNamesakeJsonRpcConsumer.get_rpc_methods(), ['method1'])
        self.assertEquals(Context2.TestNamesakeJsonRpcConsumer.get_rpc_methods(), ['method2'])

    def test_no_rpc_methods(self):
        class TestNamesakeJsonRpcConsumer(JsonRpcWebsocketConsumerTest):
            pass

        self.assertEquals(TestNamesakeJsonRpcConsumer.get_rpc_methods(), [])

    def test_jsonRpcexception_dumping(self):
        import json
        exception = JsonRpcException(1, JsonRpcWebsocketConsumerTest.GENERIC_APPLICATION_ERROR, data="test_data")
        json_res = json.loads(str(exception))
        self.assertEqual(json_res["id"], 1)
        self.assertEqual(json_res["jsonrpc"], "2.0")
        self.assertEqual(json_res["error"]["data"], "test_data")
        self.assertEqual(json_res["error"]["code"], JsonRpcWebsocketConsumerTest.GENERIC_APPLICATION_ERROR)

