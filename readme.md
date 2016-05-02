# Technology Scavenger
This application craws a set of domains looking for usages of a given list of web services. This application creates a bunch of threads and goes through the list of domains, doing a HTTP request to each one and trying to find domains in the HTML.

## Usage:
`
$ python run.py <file with domains>
`

Other options:

* ``-p``, ``--properties`` - the location of the property file
* ``-m``, ``--mode`` - what execution mode to use
* ``-j``, ``--phantomjs-bin`` - where the PhantomJS binary is located (only necessary if using the PhantomJS dectection mode)
* ``-t``, ``--threads`` - how many threads should the application spwan

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

## PhantomJS Mode
PhantomJS is an application that allows to run a website on the terminal. With this application we can simulate the pages we are visiting and find what URLs the page is requesting, as well the final loaded DOM. However this application requeres much more CPU power and memory since we are loading a page into a WebKit simulated view. To use this mode you first need to install PhantomJS using:

```
$ npm install phantomjs
```
If you already have it installed on your system, use the flat ``--phantomjs-bin`` to point where. To use this app with PhantomJS just pass the flag ``-m phantomjs``:

```
$ python run.py -m phantomjs <file with domains>
```


## Tests
To run tests just run nosetests:
```
$ nosetests
```

To check coverage, use the flag ``--with-coverage``:
```
$ nosetests --with-coverage
```


