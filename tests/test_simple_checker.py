#! /usr/bin/python

# -*- Mode: Python -*-
# -*- coding: UTF-8 -*-
# Copyright (C) 2016 by Artur Ventura
#
# File: test_simple_checker.py
# Time-stamp: Wed Apr 27 18:46:00 2016
#
# Author: Artur Ventura
#

import unittest
import threading
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer

from techscav import Property, SimpleChecker

PORT_NUMBER = 9595

class MockServer(threading.Thread):
    def __init__(self):
      super(MockServer, self).__init__()
      self.daemon = True
      self.server = HTTPServer(('', PORT_NUMBER), MockServerHandler)

    def run(self):
      self.server.handle_request()

    def close(self):
      self.server.server_close()


class MockServerHandler(BaseHTTPRequestHandler):
  
  def log_message(self, *args, **kwargs):
    pass

  #Handler for the GET requests
  def do_GET(self):
    self.send_response(200)
    self.send_header('Content-type','text/html')
    self.end_headers()
    # Send the html message
    self.wfile.write("""
<html>
<head></head>
<body>
  <a href="http://foo.com">
  <a href="http://bar.com">
</html>
""")
    return

class TestSimpleChecker(unittest.TestCase):

    def setUp(self):
      self.server = MockServer()
      self.server.start()

    def test_simple(self):
      prop = Property.from_config({
        "properties":[
          {
            "name": "Foo",
            "domains": [
              "foo.com"

            ]
          }
        ]
      })
      checker = SimpleChecker(prop)

      res = checker.check("http://localhost:%d" % PORT_NUMBER, None)


    def tearDown(self):
      self.server.close()

if __name__ == '__main__':
    unittest.main()