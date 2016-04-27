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

import time
import random
import re
import requests
import argparse
import threading
import json

from subprocess import Popen, PIPE
from multiprocessing import Process, JoinableQueue, cpu_count, Manager as mgmt

from functools import reduce


def _gen_random_sha():
    """
    Generates a random SHA1 hash for identification
    """
    return "%032x" % random.getrandbits(128)


class Property(object):
    """
    A web property that we wish to find on some domains

    Attributes:
      name        a readable name for this property
      domains     the list of domains for this property
      key         a SHA1 key to identify this property
      re          a regular expression that matches with any url from any
                  of these domains
    """

    def __init__(self, name, domains):
        self.name = name
        self.domains = domains
        self.key = _gen_random_sha()
        self.re = reduce(
            lambda x, y: "%s|%s" %
            (x, y), map(
                lambda x: "[.\\/]" + re.escape(x), domains))

    @classmethod
    def from_config(cls, propdict):
        """
        Transforms the properties.json represention into a runtime model
        """
        properties = {}

        for p in map(
                lambda x: Property(
                    x['name'],
                    x['domains']),
                propdict['properties']):
            properties[p.key] = p
        return properties


class SimpleChecker(object):
    """
    Makes a request to a URL and checks the RAW source HTML source code for the
    presence of links to domains in any of the web properties we are searching

    Attributes:
      properties   a dict of "Property" by key

    """

    def __init__(self, properties):
        self.properties = properties

    def check(self, url):
        """
        Makes a request to a URL and checks for links with domains of the web
        properties we are searching
        """
        result = []
        try:
            r = requests.get(url, timeout=10)
        except:
            return result
        for p in self.properties.values():
            if re.search(p.re, r.text):
                result.append(p.key)
        return result


class PhantomJSChecker(object):

    def __init__(self, properties, binary):
        self.properties = properties
        self.binary = binary

    def check(self, url):
        process = Popen(['/usr/bin/env', 'node', self.binary,
                         'pjs.js', url], stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()
        result = []
        print stdout
        for key, p in self.properties.items():
            if re.search(p.re, stdout):
                result.append(p.key)
        return result


class Request(object):
    """
    A request to a url.

    Attributes:
      url          the url that needs to be searched
      domain       the domain where this request comes from
    """

    def __init__(self, url, domain):
        self.url = url
        self.domain = domain

    def execute(self, checker):
        """
        Calls the checker with this url
        """
        return checker.check(self.url)


class DomainsFile(object):
    """
    A wrapper around a file object to read the file as needed, and with multiple
    threads fetching new lines.

    Attributes:
      finished     has reached the end of file
      nr           number of lines read from the file
    """

    def __init__(self, f):
        self.file = f
        self.finished = False
        self.nr = 0

    def fetch_new_domain(self):
        """
        Reads a single domain from the file
        """
        domain = self.file.readline()
        domain = domain.strip()
        if domain == '':
            self.finished = True
            return None
        self.nr += 1
        return domain


def work(process, manager):
    """
    A multiprocess worker. It just fetches requests to be made and executes them
    """
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
    """
    A central object that manages the processes start, fetching data, and 
    formating the output

    Attributes:
      queue        The shared data structure among processes, where we push 
                   requests to be made and each process pops one and does it.
      smp          number of processes to be spawn
      checker      an instance of a type of checking algorithm
      domains      the results for the domains where we found other services
      properties   the properties to searched
    """

    def __init__(self, domainsFile, properties, smp, checker):
        self.queue = JoinableQueue()
        self.domainsFile = domainsFile
        self.smp = smp
        self.checker = checker
        self.domains = mgmt().dict()
        self.properties = properties

    def add_new_request(self, request):
        """
        Adds a new request to the queue of requests
        """
        self.queue.put(request)

    def fetch_new_request(self):
        """
        Gets a request from the queue
        """
        try:
            return self.queue.get(True, 1)
        except:
            return None

    def fetch_domains(self):
        """
        Adds a bunch of domains to the queue
        """
        for i in xrange(self.smp * 2):
            domain = self.domainsFile.fetch_new_domain()
            if domain:
                r = Request("http://%s" % domain, domain)
                self.add_new_request(r)

    def start(self):
        """
        The main loop
        """
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
        """
        Formats the results and prints them
        """
        for domain, matches in self.domains.items():
            names = map(lambda x: self.properties[x].name, set(matches))
            print "%s: %s" % (domain, reduce(lambda x, y: "%s, %s" % (x, y), names))


def main():
    """
    The main function
    """
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
    properties = Property.from_config(propdict)

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
