if (!String.prototype.startsWith) {
    String.prototype.startsWith = function(searchString, position){
      position = position || 0;
      return this.substr(position, searchString.length) === searchString;
  };
}

var page = require('webpage').create();
var system = require('system');
var args = system.args;

page.onResourceRequested = function(request) {
  if(request['url'].startsWith("http")){
    console.log(request['url']);
  }
};

page.onResourceReceived = function(response) {
  if(response['url'].startsWith("http")){
    console.log(response['url']);
  }
};

page.onLoadFinished = function(status) {
  phantom.exit(0);
};

page.open(args[1]);
