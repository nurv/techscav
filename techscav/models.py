#! /usr/bin/python

# -*- Mode: Python -*-
# -*- coding: UTF-8 -*-
# Copyright (C) 2016 by Artur Ventura
#
# File: models.py
# Time-stamp: Wed Apr 27 18:46:00 2016
#
# Author: Artur Ventura
#

import random
import re
import requests

from subprocess import Popen, PIPE

from multiprocessing import Process, JoinableQueue, cpu_count, Manager as mgmt

import Queue as q

import time

def _gen_random_sha():
  return "%032x" % random.getrandbits(128)

class Property(object):
  @classmethod
  def from_config(cls, propdict):
    properties = {}
    
    for p in map(lambda x: Property(x['name'], x['domains']), propdict['properties']):
      properties[p.key] = p
    return properties

  def __init__(self, name, domains):
    self.name = name
    self.domains = domains
    self.key = _gen_random_sha()
    self.re = reduce(lambda x,y: "%s|%s" % (x,y),map(lambda x: "[.\\/]" + re.escape(x), domains))

class SimpleChecker(object):
  def __init__(self, properties):
    self.properties = properties

  def check(self, url):
    result = []
    try:
      r = requests.get(url,timeout=10)
    except:
      return result
    for key,p in self.properties.items():
        if re.search(p.re, r.text):
          result.append(p.key)
    return result

class PhantomJSChecker(object):
  def __init__(self, properties, binary):
    self.properties = properties
    self.binary = binary

  def check(self, url):
    process = Popen(['/usr/bin/env', 'node', self.binary, 'pjs.js', url], stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    result = []
    print stdout
    for key,p in self.properties.items():
        if re.search(p.re, stdout):
          result.append(p.key)
    return result

class Request(object):
  def __init__ (self, url, domain):
    self.url = url
    self.domain = domain

  def execute(self,checker):
    return checker.check(self.url)

from threading import Semaphore

class DomainsFile(object):
  def __init__(self, f):
    self.file = f
    self.finished = False
    self.nr = 0
  
  def fetch_new_domain(self):
    domain = self.file.readline()
    domain = domain.strip()
    if domain == '':
      self.finished = True
      return None
    self.nr += 1
    return domain

def work(process, manager):
  while True:
    req = manager.fetch_new_request()
    if not req:
      break
    print "%d Checking %s" % (process, req.url)
    res = req.execute(manager.checker)
    if res:
      manager.domains[req.domain] = res
    manager.queue.task_done()

class Manager(object):
  def __init__(self, domainsFile, properties, smp, checker):
    self.queue = JoinableQueue()
    self.domainsFile = domainsFile
    self.smp = smp
    self.off = 0
    self.checker = checker
    self.domains = mgmt().dict()
    self.properties = properties

  def add_new_request(self, request):
    self.queue.put(request)

  def fetch_new_request(self):
    try:
      return self.queue.get(True,1)
    except:
      return None

  def fetch_domains(self):
    for i in xrange(self.smp * 2):
      domain = self.domainsFile.fetch_new_domain()
      if domain:
        r = Request("http://%s" % domain, domain)
        self.add_new_request(r)

  def start(self):
    self.fetch_domains()
    
    self.workers = [Process(target=work, args=(i, self))
                    for i in xrange(self.smp)]
    
    for w in self.workers:
        w.daemon = True
        w.start()

    while True:
      time.sleep(0.1)
      if self.domainsFile.finished:
        for w in self.workers:
          w.join()
        break

      else:
        if self.queue.empty():
          self.fetch_domains()

  def dump(self):
    for domain,matches in self.domains.items():
      print "%s: %s" % (domain,reduce(lambda x,y: "%s, %s" % (x,y), map(lambda x: self.properties[x].name, matches)))

