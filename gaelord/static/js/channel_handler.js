onMessage = function(message) {
    $($.parseJSON(message.data).html).prependTo($('#log-records'));
}

flush = function() {
    $.post("http://[appid].appspot.com/log/flush", {'token': token});
}

var handlers = {
    'onopen': function() { },
    'onmessage': onMessage
};

channel = new goog.appengine.Channel(token);
socket = channel.open(handlers);