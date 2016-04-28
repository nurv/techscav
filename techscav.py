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
import logging
import robotparser
import urlparse
from subprocess import Popen, PIPE
from multiprocessing import Process, JoinableQueue, cpu_count, Manager as mgmt
from bs4 import BeautifulSoup
from functools import reduce

import hashlib

def _gen_random_sha():
    """
    Generates a random SHA1 hash for identification
    """
    return "%032x" % random.getrandbits(128)


class Domain(object):
    def __init__(self, netloc, useragent="*", use_robots=True, depth=1):
        self.netloc = netloc
        self.useragent = useragent
        self.use_robots = use_robots
        self.re = "[.\\/]" + re.escape(netloc)
        self.depth = depth
        if self.use_robots:
            self.robots = robotparser.RobotFileParser()
            self.robots.set_url("http://%s/robots.txt" % self.netloc)

    def can_i_visit(self, url):
        if self.use_robots:
            if self.robots and self.robots.mtime() == 0:
                try:
                    self.robots.read()
                except:
                    self.robots = None
            if not self.robots:
                return True
            else:
                return self.robots.can_fetch(self.useragent, url)
        else:
            return True


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
        self.re = reduce(lambda x, y: "%s|%s" % (x, y), map(lambda x: "[.\\/]" + re.escape(x), domains))

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

    def get_all_links(self, content):
        soup = BeautifulSoup(content, 'html.parser')
        return filter(lambda x: x, map(lambda x: x.get('href'), soup.find_all('a')))

    def check(self, request, manager):
        """
        Makes a request to a URL and checks for links with domains of the web
        properties we are searching
        """
        result = []
        try:
            logging.debug("Making request into %s" % request.url)
            r = requests.get(request.url, timeout=10)
        except:
            logging.debug("Some error happened, ignoring")
            return result
        text = r.text
        if request.depth > 1:
            
            a = self.get_all_links(text)
            for link in a:
                if link.startswith("//"):
                    link = "http:" + link

                if link.startswith("javascript:"):
                    continue

                if not link.startswith("http:"):
                    link = urlparse.urljoin(r.url, link)
                elif not re.search(request.domain.re, link):
                    continue
                
                r = Request(link, request.domain, request.depth - 1)
                
                if request.domain.can_i_visit(link):
                    manager.add_new_request(r)

        for p in self.properties.values():
            if re.search(p.re, text):
                logging.debug("Found %s property on %s " % (p.name, r.url))
                result.append(p.key)

        return result


class PhantomJSChecker(object):

    def __init__(self, properties, binary):
        self.properties = properties
        self.binary = binary

    def check(self, url):
        logging.debug("Making request into %s" % url)
        process = Popen(['/usr/bin/env', 'node', self.binary,
                         'pjs.js', url], stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()
        result = []
        print stdout
        for key, p in self.properties.items():
            if re.search(p.re, stdout):
                logging.debug("Found some %s property on %s " % (p.name, p.url))
                result.append(p.key)
        return result


class Request(object):
    """
    A request to a url.

    Attributes:
      url          the url that needs to be searched
      domain       the domain where this request comes from
    """

    def __init__(self, url, domain, depth):
        self.url = url
        self.domain = domain
        self.depth = depth
        m = hashlib.md5()
        m.update(url)
        self.digest = m.digest()


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
    tries = 3
    while True:        
        req = manager.fetch_new_request()

        if not req:
            if tries:
                logging.debug("Did not found anything to do, %s waiting a little" % process)
                tries -= 1
                time.sleep(5)
                continue
            else:
                logging.debug("Nothing else to do, %s dying" % process)
                break
        else:
            tries = 3
        res = manager.checker.check(req, manager)
        if res:
            manager.domains[req.domain.netloc] = res
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

    def __init__(self, domainsFile, properties, smp, checker, useragent="*", use_robots=True, depth=1):
        self.queue = JoinableQueue()
        self.domainsFile = domainsFile
        self.smp = smp
        self.checker = checker
        self.domains = mgmt().dict()
        self.properties = properties
        self.useragent = useragent
        self.use_robots = use_robots
        self.depth = depth
        self.hits = set()

    def add_new_request(self, request):
        """
        Adds a new request to the queue of requests
        """
        if request.digest not in self.hits:
            logging.debug("Addding request to queue %s d: %d" % (request.url, request.depth))
            self.queue.put(request)
            self.hits.add(request.digest)
        else:
            logging.debug("Cache hit %s d: %d" % (request.url, request.depth))

    def fetch_new_request(self):
        """
        Gets a request from the queue
        """
        try:
            return self.queue.get(True, 1)
        except:
            return None

    def read_domain(self):
        domain = self.domainsFile.fetch_new_domain()
        if domain:
            return Domain(domain, useragent=self.useragent, use_robots=self.use_robots, depth=self.depth)


    def fetch_domains(self):
        """
        Adds a bunch of domains to the queue
        """
        for i in xrange(self.smp * 2):
            domain = self.read_domain()
            if domain:
                r = Request("http://%s" % domain.netloc, domain, domain.depth)
                self.add_new_request(r)


    def start(self):
        """
        The main loop
        """
        self.fetch_domains()

        self.workers = [Process(target=work, args=(i, self))
                        for i in xrange(self.smp)]
        
        logging.debug("Spawing %s daemons" % len(self.workers))
        
        for w in self.workers:
            w.daemon = True
            w.start()

        while True:
            time.sleep(0.1)
            if self.domainsFile.finished:
                logging.debug("Looks finished, joining")
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
    parser = argparse.ArgumentParser(description='Detects the usage of web properties')
  
    parser.add_argument('file', metavar='<file>', type=argparse.FileType('r'), nargs=1,
                     help='file with the domains to be searched')
    
    parser.add_argument('-v', '--verbose', action="count", help="verbose level... repeat up to three times.")

    parser.add_argument('-p', "--properties", metavar='<properties>', type=argparse.FileType('r'), nargs=1,
                     help='file describing the properties and the domains related to them (default: sites.json)', default="properties.json")

    parser.add_argument('-i', "--ignore-robots-txt", action="store_true", help='ignores robots.txt while crawling')

    parser.add_argument('-m', "--mode", metavar='<mode>', type=str, nargs=1,
                     help='how the properties are found. Can be "simple" or "phantomjs" (default: simple)', default=["simple"])

    parser.add_argument('-j', "--phantomjs-bin", metavar='<phantomjs>', type=str, nargs=1,
                     help='the location of the phantomjs binary (default: ./node_modules/phantomjs/bin/phantomjs)', default=["./node_modules/phantomjs/bin/phantomjs"])

    parser.add_argument('-t','--threads', nargs=1, help='number of threads used (default: CPUs)', 
                     metavar='<threads>', type=int, default=[cpu_count()])

    parser.add_argument('-d','--depth', nargs=1, help='how deep the crawler should go (default: 1)', 
                     metavar='<depth>', type=int, default=[1])

    args = parser.parse_args()


    if not args.verbose:
        level = logging.ERROR
    elif args.verbose == 1:
        level = logging.WARNING
    elif args.verbose == 2:
        level = logging.INFO
    elif args.verbose >= 3:
        level = logging.DEBUG
    logging.basicConfig(format='[%(levelname)s] %(message)s', level=level)

    logging.debug("Args parsed: %s" % args)
    
    propdict = json.loads(args.properties.read())

    properties = Property.from_config(propdict)
    
    logging.debug("%s properties loaded and parsed" % len(propdict['properties']))

    if args.mode[0] == "simple":
        logging.debug("Using SimpleChecker")
        checker = SimpleChecker(properties)
    elif args.mode[0] == "phantomjs":
        logging.debug("Using PhantomJSChecker")
        checker = PhantomJSChecker(properties, args.phantomjs_bin[0])
    else:
        logging.error("unkonwn mode: %s" % args.mode)
        raise Exception("unkonwn mode: %s" % args.mode)

    manager = Manager(DomainsFile(args.file[0]), properties, args.threads[0], checker, use_robots=args.ignore_robots_txt, depth=args.depth[0])
    manager.start()
    logging.debug("Finished, dumping %s result(s)" % len(manager.domains))
    manager.dump()

if __name__ == '__main__':
    main()
