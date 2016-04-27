#! /usr/bin/python

# -*- Mode: Python -*-
# -*- coding: UTF-8 -*-
# Copyright (C) 2016 by Artur Ventura
#
# File: run.py
# Time-stamp: Wed Apr 27 18:46:00 2016
#
# Author: Artur Ventura
#

import argparse
import threading
import json
from multiprocessing import cpu_count

from techscav.models import load_properties_from_config, Property, DomainsFile, Manager, SimpleChecker, PhantomJSChecker

def main():
  parser = argparse.ArgumentParser(description='Detects the usage of online properties')
  
  parser.add_argument('file', metavar='<file>', type=argparse.FileType('r'), nargs=1,
                     help='files with the domains to be searched')

  parser.add_argument('-p', "--properties", metavar='<properties>', type=argparse.FileType('r'), nargs=1,
                     help='file describing the properties and the domains related to them (default: sites.json)', default="properties.json")

  parser.add_argument('-m', "--mode", metavar='<mode>', type=str, nargs=1,
                     help='how the properties are found. Can be "simple", "semantic" or "phantomjs" (default: simple)', default=["simple"])

  parser.add_argument('-j', "--phantomjs-bin", metavar='<phantomjs>', type=str, nargs=1,
                     help='the location of the phantomjs binary (default: ./node_modules/phantomjs/bin/phantomjs)', default=["./node_modules/phantomjs/bin/phantomjs"])

  parser.add_argument('-t','--threads', nargs=1, help='number of threads used (default: CPUs)', 
                     metavar='<threads>', type=int, default=[cpu_count()])

  args = parser.parse_args()

  propdict = json.loads(args.properties.read())
  properties = load_properties_from_config(propdict)

  if args.mode[0] == "simple":
    checker = SimpleChecker(properties)
  elif args.mode[0] == "phantomjs":
    checker = PhantomJSChecker(properties, args.phantomjs_bin[0])
  else:
    raise Exception("unkonwn mode: %s" % args.mode)

  manager = Manager(DomainsFile(args.file[0]), properties, args.threads[0], checker)
  manager.start()

  manager.dump()

if __name__ == '__main__':
  main()