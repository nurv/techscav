#! /usr/bin/python

# -*- Mode: Python -*-
# -*- coding: UTF-8 -*-
# Copyright (C) 2016 by Artur Ventura
#
# File: test_test_domain.py
# Time-stamp: Wed Apr 27 18:46:00 2016
#
# Author: Artur Ventura
#

import unittest
from mock import Mock

from techscav import Domain
from mocks import MockFile
import threading
import re

from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer

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
    self.wfile.write("""User-agent: *
Disallow: /search
""")
    return

class TestDomain(unittest.TestCase):

  def test_create(self):
    d = Domain("domain.com", use_robots=False, depth=2)

    self.assertEqual(d.netloc, "domain.com")
    self.assertEqual(d.depth, 2)

    self.assertTrue(re.search(d.re, "http://domain.com/home"))
    self.assertTrue(re.search(d.re, "http://talk.domain.com/home"))
    self.assertFalse(re.search(d.re, "http://landsdomain.com/home"))

    self.assertTrue(d.can_i_visit("http://domain.com/home"))

  def test_robots(self):
    server = MockServer()
    server.start()

    d = Domain("localhost:%d" % PORT_NUMBER, use_robots=True)
    self.assertTrue(d.can_i_visit("http://domain.com/home"))
    self.assertFalse(d.can_i_visit("http://domain.com/search"))
    server.close()

if __name__ == '__main__':
    unittest.main()
