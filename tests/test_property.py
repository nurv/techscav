#! /usr/bin/python

# -*- Mode: Python -*-
# -*- coding: UTF-8 -*-
# Copyright (C) 2016 by Artur Ventura
#
# File: test_property.py
# Time-stamp: Wed Apr 27 18:46:00 2016
#
# Author: Artur Ventura
#

import unittest

import re

from techscav import Property

class TestPropertyLoad(unittest.TestCase):
  def test_load_properties_from_config(self):
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
    self.assertEqual(len(p), 1)
    self.assertEqual(p.keys()[0],p.values()[0].key)

class TestProperty(unittest.TestCase):

  def test_create_single(self):
      p = Property("Foo", ["foo.com"])
      self.assertEqual('Foo', p.name)
      self.assertIn('foo.com', p.domains)
      self.assertTrue(re.search(p.re, "--http://foo.com--"))
      self.assertFalse(re.search(p.re, "--http://bar.com--"))

      self.assertTrue(re.search(p.re, "--http://delta.foo.com--"))

  def test_create_multiple(self):
      p = Property("Foo", ["foo.com", "bar.com"])
      self.assertEqual('Foo', p.name)
      self.assertIn('foo.com', p.domains)
      self.assertIn('bar.com', p.domains)

  def test_regexp_single(self):
      p = Property("Foo", ["foo.com"])
      self.assertTrue(re.search(p.re, "--http://foo.com--"))
      self.assertFalse(re.search(p.re, "--http://bar.com--"))

      self.assertTrue(re.search(p.re, "--http://delta.foo.com--"))

  def test_regexp_multiple(self):
      p = Property("Foo", ["foo.com", "bar.com"])
      self.assertTrue(re.search(p.re, "--http://foo.com--"))
      self.assertTrue(re.search(p.re, "--http://bar.com--"))      
      self.assertFalse(re.search(p.re, "--http://data.com--"))

      self.assertTrue(re.search(p.re, "--http://vega.foo.com--"))
      self.assertTrue(re.search(p.re, "--http://meta.bar.com--"))

if __name__ == '__main__':
    unittest.main()
