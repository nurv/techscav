#! /usr/bin/python

# -*- Mode: Python -*-
# -*- coding: UTF-8 -*-
# Copyright (C) 2016 by Artur Ventura
#
# File: test_domains_file.py
# Time-stamp: Wed Apr 27 18:46:00 2016
#
# Author: Artur Ventura
#

import unittest
from mock import Mock

from techscav.models import DomainsFile
from mocks import MockFile

class TestDomainsFile(unittest.TestCase):

  def test_create(self):
      r = DomainsFile(MockFile("""foo.com
bar.com
"""))
      self.assertEqual(r.nr, 0)
      self.assertFalse(r.finished)
      self.assertEqual(r.fetch_new_domain(), "foo.com")
      self.assertEqual(r.nr, 1)
      self.assertFalse(r.finished)
      self.assertEqual(r.fetch_new_domain(), "bar.com")
      self.assertEqual(r.nr, 2)
      self.assertFalse(r.finished)
      self.assertEqual(r.fetch_new_domain(), None)
      self.assertEqual(r.nr, 2)
      self.assertTrue(r.finished)
      self.assertEqual(r.fetch_new_domain(), None)
      self.assertEqual(r.nr, 2)
      self.assertTrue(r.finished)

if __name__ == '__main__':
    unittest.main()
