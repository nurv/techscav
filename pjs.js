if (!String.prototype.startsWith) {
    String.prototype.startsWith = function(searchString, position){
      position = position || 0;
      return this.substr(position, searchString.length) === searchString;
  };
}

var page = require('webpage').create();
var system = require('system');
var args = system.args;
var urls = []

page.onResourceRequested = function(request) {
  if(request['url'].startsWith("http")){
    urls.push(request['url'])
  }
};

page.onResourceReceived = function(response) {
  if(response['url'].startsWith("http")){
    urls.push(response['url'])
  }
};

page.onLoadFinished = function(status) {
  console.log(JSON.stringify({
    url:page.url,
    content:page.content,
    urls:urls
  }))
  phantom.exit(0);
};

page.open(args[1]);
