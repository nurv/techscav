#! /usr/bin/python

# -*- Mode: Python -*-
# -*- coding: UTF-8 -*-
# Copyright (C) 2016 by Artur Ventura
#
# File: test_request.py
# Time-stamp: Wed Apr 27 18:46:00 2016
#
# Author: Artur Ventura
#

import unittest
from mock import Mock

from techscav import Domain, Request

class TestRequest(unittest.TestCase):

  def test_create(self):
      d = Domain("domain.com", use_robots=False, depth=2)
      r = Request("http://foo.com", d, 1)

      self.assertEqual(r.url, "http://foo.com")
      self.assertEqual(r.domain, d)
      self.assertEqual(r.depth, 1)


if __name__ == '__main__':
    unittest.main()
