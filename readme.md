# Technology Scavenger
This application craws a set of domains looking for usages of a given list of web services. This application creates a bunch of threads and goes through the list of domains, doing a HTTP request to each one and trying to find domains in the HTML.


## Usage:
`
$ python run.py <file with list of domains>
`

Other options:

* ``-p``, ``--properties`` - the location of the property file
* ``-m``, ``--mode`` - what execution mode to use
* ``-j``, ``--phantomjs-bin`` - where the PhantomJS binary is located (only necessary if using the PhantomJS dectection mode)
* ``-t``, ``--threads`` - how many threads should the application spwan
* ``-d``, ``--depth`` - how deep into the site should the crawler go
* ``-d``, ``--depth`` - how deep into the site should the crawler go
* ``-i``, ``--ignore-robots-txt`` - ignores the robots.txt
* ``-v``, ``--verbose`` - verbosity, add up to 3 times for more information

Check ``--help`` for more information.

## Properties File
The properties file describes what web servies the system should be looking for. Each property can have more than one domain associated (e.g. Google → ``google.com``, ``google.pt``, ``gmail.com``, etc.). Below is a sample:

```
{
  "properties":[
    {
      "name": "Foo",
      "domains": [
        "foo.com"
      ]
    },
    {
      "name": "Bar",
      "domains": [
        "bar.com",
        "deleta.com"
      ]
    }
  ]
}
```

## Instalation:
To run we sugest the usage of VirtualEnv:

`
$ cd techscav
$ virtualenv .env
...
$ source .env/bin/activate
`

You need to install the dependencies:
`
$ pip install -r requirements.txt
`

## Tests
To run tests just run nosetests:
```
$ nosetests
```

To check coverage, use the flag ``--with-coverage``:
```
$ nosetests --with-coverage
```


