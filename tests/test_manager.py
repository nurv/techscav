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
from mocks import MockFile
from techscav import Manager, Property

class TestManager(unittest.TestCase):

  def test_create(self):
    f = MockFile("""""")
    p = Property.from_config({
      "properties":[
        {
          "name": "Foo",
          "domains": [
            "foo.com"

          ]
        }
      ]
    })
    m = Manager(f, p, 1, None)


if __name__ == '__main__':
    unittest.main()
