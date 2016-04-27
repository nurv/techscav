#! /usr/bin/python

# -*- Mode: Python -*-
# -*- coding: UTF-8 -*-
# Copyright (C) 2016 by Artur Ventura
#
# File: test_manager.py
# Time-stamp: Wed Apr 27 18:46:00 2016
#
# Author: Artur Ventura
#

import unittest
from mock import Mock

from techscav.models import Request

class TestManager(unittest.TestCase):

  def test_create(self):
    f = MockFile("""""")
    p
    r = Manager(f, p, 1, None)

      self.assertEqual(r.url, "http://foo.com")
      self.assertEqual(r.domain, "foo.com")

  def test_execute(self):

    mockChecker = Mock()
    mockChecker.check.return_value = "YES!"
    
    r = Request("http://foo.com", "foo.com")    
    res = r.execute(mockChecker)
    
    self.assertEqual(res, "YES!")


if __name__ == '__main__':
    unittest.main()
