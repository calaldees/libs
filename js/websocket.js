// Websocket -------------------------------
var socket_retry_interval = null;

// Authenicate client with session key on socket connect
function _websocket_first_message_auth(socket, session_cookie_name) {
	session_cookie_name = session_cookie_name || "_session";
	socket.send(document.cookie.match(/session_cookie_name=([^;\s]+)/)[1]);  // Um? this needs to be a variable
}

function setup_websocket(on_connect, on_message, options) {
	console.debug("setup_websocket", options);
	
	//default options
	options = _.extend({
		port: 9873,
		format: 'json',
		auth: function(socket) {},
		disconnected_retry_interval: 5,
	}, options) 
	
	$('body').addClass('websocket_disconnected');

	var socket = new WebSocket("ws://"+location.hostname+":"+options.port+"/");

	socket.onopen = function() {
		options.auth(socket);  // optional function to auth once connected
		$('body').removeClass('websocket_disconnected');
		if (socket_retry_interval) {
			clearInterval(socket_retry_interval);
			socket_retry_interval = null;
		}
		console.debug("websocket: Connected");
		on_connect();
	};
	socket.onclose  = function() {
		socket = null;
		$('body').addClass('websocket_disconnected');
		console.debug("websocket: Disconnected");
		if (!socket_retry_interval) {
			socket_retry_interval = setInterval(function(){setup_websocket(on_connect, on_message, options)}, options.disconnected_retry_interval * 1000);
		}
	};
	socket.onmessage = function(msg) {
		msg = msg.data;
		if (options.format=='json') {
			msg = JSON.parse(msg);
		}
		on_message(msg);
	};
	
}
