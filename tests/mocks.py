#! /usr/bin/python

# -*- Mode: Python -*-
# -*- coding: UTF-8 -*-
# Copyright (C) 2016 by Artur Ventura
#
# File: mocks.py
# Time-stamp: Wed Apr 27 18:46:00 2016
#
# Author: Artur Ventura
#

class MockFile(object):
  def __init__(self, text):
    self.i = 0
    self.text = text.split("\n")

  def readline(self):
    if self.i >= len(self.text):
      return ""
    else:
      t = self.text[self.i]
      self.i += 1
      return t