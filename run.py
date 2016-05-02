import json
import argparse
import logging

from techscav import *

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
    try:
        manager.start()
    except:
        logging.debug("Exception on the main thread, bailing...")    
    logging.debug("Finished, dumping %s result(s)" % len(manager.domains))
    manager.dump()

if __name__ == '__main__':
    main()