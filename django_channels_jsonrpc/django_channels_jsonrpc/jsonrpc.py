# -*- coding:utf-8 -*-

# Copyright (c) 2010 Atsushi Odagiri
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.



import sys
import json
import logging
import itertools
from six import string_types

logger = logging.getLogger(__name__)


class JsonRpcBase(object):
    def __init__(self, methods=None,
                 application_errors={}):
        if methods is not None:
            self.methods = methods
        else:
            self.methods = {}

        message = ('extra error code must '
                   'be from {0} to {1}').format(-32099, -32001)
        for code in application_errors.values():
            if code < -32100 or code > -32001:
                raise ValueError(message, code)
        self.application_errors = application_errors.copy()
        self.exceptable = tuple(application_errors)

    def load_method(self, method):
        module_name, func_name = method.split(':', 1)
        __import__(module_name)
        method = getattr(sys.modules[module_name], func_name)
        return method

    def get_app_error_code(self, exc):
        exc_type = type(exc)
        return self.application_errors[exc_type]

    def process(self, data, extra_vars):

        if data.get('jsonrpc') != "2.0":
            raise JsonRpcException(data.get('id'), INVALID_REQUEST)

        if 'method' not in data:
            raise JsonRpcException(data.get('id'), INVALID_REQUEST)

        methodname = data['method']
        if not isinstance(methodname, string_types):
            raise JsonRpcException(data.get('id'), INVALID_REQUEST)

        if methodname.startswith('_'):
            raise JsonRpcException(data.get('id'), METHOD_NOT_FOUND)

        if methodname not in self.methods:
            raise JsonRpcException(data.get('id'), METHOD_NOT_FOUND)

        method = self.methods[methodname]
        params = data.get('params', [])

        if isinstance(method, string_types):
            method = self.load_method(method)

        if not isinstance(params, (list, dict)):
            raise JsonRpcException(data.get('id'), INVALID_PARAMS)

        args = []
        kwargs = {}
        if isinstance(params, list):
            args = params
        elif isinstance(params, dict):
            kwargs.update(params)
            kwargs.update(extra_vars)

        try:
            result = method(*args, **kwargs)
        except self.exceptable as e:
            return {
                'jsonrpc': '2.0',
                'id': data.get('id'),
                'error': {'code': self.get_app_error_code(e),
                          'message': str(e),
                          'data': json.dumps(e.args)}
            }
        except Exception as e:
            return {
                'jsonrpc': '2.0',
                'id': data.get('id'),
                'error': {'code': GENERIC_APPLICATION_ERROR,
                          'message': str(e),
                          'data': json.dumps(e.args)}
            }

        if not data.get('id'):
            return None
        return {
            'jsonrpc': '2.0',
            'id': data.get('id'),
            'result': result,
        }

    def _call(self, data, extra_vars):
        try:
            return self.process(data, extra_vars)
        except JsonRpcException as e:
            return e.as_dict()

    def __call__(self, data, **extra_vars):
        if isinstance(data, dict):
            resdata = self._call(data, extra_vars)
        elif isinstance(data, list):
            if len([x for x in data if not isinstance(x, dict)]):
                resdata = {'jsonrpc': '2.0',
                           'id': None,
                           'error': {'code': INVALID_REQUEST,
                                     'message': errors[INVALID_REQUEST]}}
            else:
                resdata = [d for d in (self._call(d, extra_vars) for d in data) if d is not None]

        return resdata

    def __getitem__(self, key):
        return self.methods[key]

    def __setitem__(self, key, value):
        self.methods[key] = value

    def __delitem__(self, key):
        del self.methods[key]

