import json
from json import JSONEncoder
import argparse
import logging
import zmq
import time

from structures import DomainsFile, Property, Domain, Request

class ServerManager(object):
    """
    A central object that manages the processes start, fetching data, and 
    formating the output

    Attributes:
        queue       The shared data structure among processes, where we push 
                    requests to be made and each process pops one and does it.
        smp         number of processes to be spawn
        checker     an instance of a type of checking algorithm
        domains     the results for the domains where we found other services
        properties  the properties to searched
        useragent   the useragent to use
        use_robots  should the crawler be restricted to the rules of robots.txt
        depth       how deep should we go while searching a domain
        hits        a cache of previously visited urls
    """

    def __init__(self, domainsFile, properties, useragent="*", use_robots=True, depth=1):
        self.domainsFile = domainsFile
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
            # self.queue.put(request)
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
        """
        Read a domain from the domain files
        """
        domain = self.domainsFile.fetch_new_domain()
        if domain:
            return Domain(domain, useragent=self.useragent, use_robots=self.use_robots, depth=self.depth)


    def fetch_domains(self):
        """
        Adds a bunch of domains to the queue
        """
        for i in xrange(10):
            domain = self.read_domain()
            if domain:
                r = Request("http://%s" % domain.netloc, domain, domain.depth)
                self.add_new_request(r)


    def start(self):
        """
        The main loop
        """

        self.fetch_domains()

        port = "5757"

        context = zmq.Context()
        socket = context.socket(zmq.REP)
        socket.bind("tcp://*:%s" % port)

        while True:
            #  Wait for next request from client
            message = socket.recv()
            properties = json.loads(message)
            if properties['type'] == "D":
                data = { 'type':'O', 'properties':{ key: value.to_remote() for key, value in self.properties.items() } }

            else:
                data = { 'type': 'E', 'reason': "don't know what that means" }
            print data
            socket.send(json.dumps(data))
            print "Received request: ", message
            
        
        # for w in self.workers:
        #     w.daemon = True
        #     w.start()

        # while True:
        #     time.sleep(0.1)
        #     if self.domainsFile.finished:
        #         logging.debug("Looks finished, joining")
        #         for w in self.workers:
        #             w.join()
        #         break

        #     else:
        #         if self.queue.empty():
        #             self.fetch_domains()

    def dump(self):
        """
        Formats the results and prints them
        """
        for domain, matches in self.domains.items():
            names = map(lambda x: self.properties[x].name, set(matches))
            print "%s: %s" % (domain, reduce(lambda x, y: "%s, %s" % (x, y), names))

class ClientWorkerManager(object):
    def __init__(self, properties):
        port = "5757"

        context = zmq.Context()
        print "Connecting to server..."
        self.socket = context.socket(zmq.REQ)
        self.connect ("tcp://localhost:%s" % port)

    def add_new_request(self, request):
        """
        Adds a new request to the queue of requests
        """
        self.sock.send(json.dumps({ 'type':'A', 'url':request.url, 'depth':request.depth }))
        res = json.loads(self.sock.recv())
        if not res['type'] == 'O':
            raise Exception("Error adding")

    def fetch_new_request(self):
        """
        Gets a request from the queue
        """
        self.sock.send(json.dumps({ 'type':'R' }))
        res = json.loads(self.sock.recv())
        if res['type'] == 'O':
            return Request.from_remote(res['request'])


class ClientManager(object):
    """
    A central object that manages the processes start, fetching data, and 
    formating the output

    Attributes:
        queue       The shared data structure among processes, where we push 
                    requests to be made and each process pops one and does it.
        smp         number of processes to be spawn
        checker     an instance of a type of checking algorithm
        domains     the results for the domains where we found other services
        properties  the properties to searched
        useragent   the useragent to use
        use_robots  should the crawler be restricted to the rules of robots.txt
        depth       how deep should we go while searching a domain
        hits        a cache of previously visited urls
    """

    def __init__(self, server):
        self.server = server
        self.hits = set()

    def read_domain(self):
        """
        Read a domain from the domain files
        """
        domain = self.domainsFile.fetch_new_domain()
        if domain:
            return Domain(domain, useragent=self.useragent, use_robots=self.use_robots, depth=self.depth)


    def fetch_domains(self):
        """
        Adds a bunch of domains to the queue
        """
        # for i in xrange(self.smp * 2):
        #     domain = self.read_domain()
        #     if domain:
        #         r = Request("http://%s" % domain.netloc, domain, domain.depth)
        #         self.add_new_request(r)


    def start(self):
        """
        The main loop
        """

        port = "5757"

        context = zmq.Context()
        print "Connecting to server..."
        socket = context.socket(zmq.REQ)
        socket.connect ("tcp://localhost:%s" % port)

        #  Do 10 requests, waiting each time for a response
        
        print "Sending request "
        socket.send (json.dumps({ 'type' : 'D'}))
        s = socket.recv()

        self.properties = {key: Property.from_remote(value) for key, value in json.loads(s)['properties'].items()}
        print self.properties


    
        
        # for w in self.workers:
        #     w.daemon = True
        #     w.start()

        # while True:
        #     time.sleep(0.1)
        #     if self.domainsFile.finished:
        #         logging.debug("Looks finished, joining")
        #         for w in self.workers:
        #             w.join()
        #         break

        #     else:
        #         if self.queue.empty():
        #             self.fetch_domains()

    def dump(self):
        """
        Formats the results and prints them
        """
        for domain, matches in self.domains.items():
            names = map(lambda x: self.properties[x].name, set(matches))
            print "%s: %s" % (domain, reduce(lambda x, y: "%s, %s" % (x, y), names))

def main():

    parser = argparse.ArgumentParser(description='Detects the usage of web properties')
  

    parser.add_argument('file', metavar='<file>', type=argparse.FileType('r'), nargs=1,
                     help='file with the domains to be searched')

    parser.add_argument('-p', "--properties", metavar='<properties>', type=argparse.FileType('r'), nargs=1,
                     help='file describing the properties and the domains related to them (default: sites.json)', default="properties.json")

    parser.add_argument('-c', "--client", metavar='<server>', type=str, nargs=1,
                     help='turn on client mode', default=None)

    parser.add_argument('-s', "--server", action="store_true", help='turn on server mode', default=None)

    args = parser.parse_args()

    propdict = json.loads(args.properties.read())

    properties = Property.from_config(propdict)
    if args.server:
        manager = ServerManager(DomainsFile(args.file[0]), properties, 1)
    else:
        manager = ClientManager(args.client[0])
    manager.start()

if __name__ == '__main__':
    main()